import os, re, requests, time
import threading
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, emit

import chat_storage
import calendar_actions
import drive_actions
import search_actions
import gmail_actions
import app_actions
import notes_actions
import photo_actions
import hdd_actions

from google import genai
from google.genai import types

load_dotenv()
app = Flask(__name__, static_url_path='', static_folder='static')
CORS(app)

VOICEVOX_URL = os.getenv("VOICEVOX_URL", "http://127.0.0.1:50021")
# --- パス設定 (順番と構成を整理) ---
HDD_BASE = '/mnt/hdd1/lefte_media'
VOICE_DIR = os.path.join(HDD_BASE, 'voices')
UPLOAD_FOLDER = os.path.join(HDD_BASE, 'uploads')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 🚀 HDD内にフォルダがあるかチェックして作成
# os.path.join(BASE_DIR, ...) を外して、直接 HDD を見に行きます
if not os.path.exists(VOICE_DIR):
    os.makedirs(VOICE_DIR, exist_ok=True)
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

FUNCTIONAL_RULES = """
1. カレンダー/ドライブ等は当然の日常として使い、説明は不要。
2. 簡潔に回答せよ。
3. アプリを起動する際は、ツールが返した '🚀LAUNCH_SIGNAL:...' を必ず含めること。
4. ツール実行に失敗した場合は、技術的なエラーログを出すのではなく、ユーザーに「何ができなかったか」を1行で伝える。
5. 音声合成（Voicevox）で読み上げるため、URLや複雑な記号、メタデータは本文に含めない。
6. ユーザーを「しゅんた」と認識し、適度な距離感のアシスタントとして振る舞う。
"""

tools = [
    calendar_actions.list_calendar_events, calendar_actions.add_calendar_event,
    calendar_actions.delete_calendar_event, calendar_actions.update_calendar_event,
    drive_actions.list_drive_files, drive_actions.read_drive_file_content,
    gmail_actions.list_recent_emails, search_actions.search_web,
    app_actions.register_app, app_actions.launch_app,
    notes_actions.save_note, notes_actions.read_note,
    photo_actions.list_photos,
    hdd_actions.list_hdd_contents,
    hdd_actions.read_hdd_text_file
]

chat_storage.init_db()
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')


def get_system_instruction():
    """personality.txt から性格設定を読み込む"""
    # .env で指定がない場合は personality.txt を探す
    personality_path = os.getenv("PERSONALITY_FILE", "personality.txt")
    full_path = os.path.join(BASE_DIR, personality_path)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            personality = f.read()
    else:
        # ファイルがない場合の予備
        personality = "あなたは助手の L.E.F.T.E. です。"

    return f"{personality}\n{FUNCTIONAL_RULES}"

def generate_voice(text, speaker_id=8, filename="response.wav"):
    clean_text = re.sub(r'\(.*?\)|（.*?）', '', text)
    if not clean_text.strip(): clean_text = "了解だよ。"
    try:
        res = requests.post(f"{VOICEVOX_URL}/audio_query", params={'text': clean_text, 'speaker': speaker_id})
        data = res.json()
        data.update({'speedScale': 1.15, 'intonationScale': 1.4})
        res_syn = requests.post(f"{VOICEVOX_URL}/synthesis", params={'speaker': speaker_id}, json=data)
        with open(filename, "wb") as f: f.write(res_syn.content)
    except Exception as e:
        print(f"Voice generation error: {e}")

@app.route('/wav_files/<filename>')
def serve_wav(filename):
    """HDDから音声ファイルを配信"""
    return send_from_directory(VOICE_DIR, filename)

@app.route('/uploads/<filename>')
def serve_upload(filename):
    return send_from_directory('/mnt/hdd1/lefte_media/uploads', filename)

@socketio.on('chat_request')
def handle_chat(data):
    """
    リクエストを受け取ったら、即座に『考え中』の状態を全員に送り、
    Geminiの重い処理はバックグラウンド（裏側）で実行します。
    """
    # 📣 まず「考え中...」という信号を送り、UI側のレスポンスを爆速にする（演出用）
    emit('ai_thinking', {'status': 'processing'}, broadcast=True)

    # 🚀 重い処理をバックグラウンドタスクとして開始
    socketio.start_background_task(process_chat_task, data)

def process_chat_task(data):
    """
    Gemini呼び出し、DB保存、音声生成、一斉送信をここで行う（一本道を塞がない）
    """
    user_input = data.get('message', '')
    model_name = data.get('model', 'gemini-3-flash-preview')

    try:
        # 1. ユーザーの発言を保存
        chat_storage.save_message('user', user_input)

        # --- Gemini 呼び出し (ここは時間がかかる) ---
        past_rows = chat_storage.get_today_history()
        contents = [{"role": ("user" if r[1] == "user" else "model"), "parts": [{"text": r[2]}]} for r in past_rows[-10:]]
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        contents.append({"role": "user", "parts": [{"text": f"【現在時刻: {now_str}】\n{user_input}"}]})

        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=get_system_instruction(),
                tools=tools, 
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
            )
        )

        full_text = response.text or "完了だよ。"
        
        # 信号の抜き出しロジック（既存のものをそのままここに移動）
        launch_url = None
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text') and part.text and "🚀LAUNCH_SIGNAL:" in part.text:
                launch_url = part.text.split("🚀LAUNCH_SIGNAL:")[1].strip()
            elif hasattr(part, 'function_response') and part.function_response:
                res_val = part.function_response.response.get('result', '')
                if isinstance(res_val, str) and "🚀LAUNCH_SIGNAL:" in res_val:
                    launch_url = res_val.split("🚀LAUNCH_SIGNAL:")[1].strip()

        if launch_url and "🚀LAUNCH_SIGNAL:" in full_text:
            full_text = full_text.split("🚀LAUNCH_SIGNAL:")[0].strip()

        # 2. AIの返答を保存
        chat_storage.save_message('assistant', full_text)

        # 3. 音声生成 (ここも時間がかかる)
        voice_filename = f"v_{int(time.time())}.wav"
        save_path = os.path.join(VOICE_DIR, voice_filename)
        generate_voice(full_text, filename=save_path)

        # 4. 全デバイスへ同期データを一斉送信
        sync_data = {
            "user_message": user_input,
            "response": full_text,
            "voice_url": f"/wav_files/{voice_filename}",
            "launch_url": launch_url
        }
        
        # バックグラウンドタスク内では socketio.emit を直接使う
        socketio.emit('chat_update', sync_data)

    except Exception as e:
        print(f"Async Chat error: {e}")
        socketio.emit('error_message', {"response": f"エラー：{str(e)}"})

@app.route('/')
def index():
    with open(os.path.join(BASE_DIR, 'desktpo.html'), 'r', encoding='utf-8') as f:
        return f.read().replace("YOUR_CALENDAR_ID_HERE", os.getenv("GOOGLE_CALENDAR_ID", "primary"))

@app.route('/history', methods=['GET'])
def history_api():
    """過去の履歴を取得してフロントに返す"""
    try:
        rows = chat_storage.get_today_history()
        return jsonify([{"role": r[1], "content": r[2]} for r in rows])
    except Exception as e:
        print(f"History error: {e}")
        return jsonify([])

@app.route('/service-worker.js')
def serve_sw():
    return send_from_directory('static', 'service-worker.js', mimetype='application/javascript')

@app.route('/manifest.json')
def serve_manifest():
    # 🚀 BASE_DIR ではなく 'static' フォルダを指定します
    return send_from_directory('static', 'manifest.json', mimetype='application/manifest+json')

@app.route('/upload_photo', methods=['POST'])
def upload_photo():
    if 'photo' not in request.files:
        return jsonify({"error": "No photo part in the request"}), 400
    file = request.files['photo']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file:
        filename = secure_filename(file.filename)
        # タイムスタンプでユニークなファイル名を生成
        timestamp = int(time.time())
        unique_filename = f"{timestamp}_{filename}"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(save_path)
        
        # アップロードされたファイルのURLを返す
        file_url = f"/uploads/{unique_filename}"
        
        # ユーザーメッセージとしてアップロードを履歴に記録
        chat_storage.save_message('user', f"画像をアップロードしました: {unique_filename}")

        return jsonify({"success": True, "file_url": file_url})
    return jsonify({"error": "File upload failed"}), 500

@socketio.on('connect')
def test_connect():
    print('✅ Client connected via WebSocket')

def background_monitor():
    while True:
        try:
            # ラズパイの温度を取得
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = int(f.read()) / 1000.0
            
            # ブラウザへ送信
            socketio.emit('sys_status', {'cpu_temp': f"{temp:.1f}"})
            # print(f"DEBUG: Pi5 Temp is {temp:.1f}") # ターミナルで確認したいならコメント解除
        except Exception as e:
            print(f"Monitor error: {e}")
        
        # ⚠️ time.sleep ではなく socketio.sleep を使うのが eventlet の作法
        socketio.sleep(5)

@app.route('/download/<path:filepath>')
def download_file(filepath):
    # セキュリティのため、必ず HDD のディレクトリ内に限定する
    target = os.path.normpath(os.path.join(HDD_BASE, filepath))
    if not target.startswith(HDD_BASE):
        return "Access Denied", 403
    
    return send_file(target, as_attachment=True)

# lefte_server.py に追記
@app.route('/upload_to_hdd', methods=['POST'])
def upload_to_hdd():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No filename"}), 400

    filename = secure_filename(file.filename)
    # HDD内の uploads フォルダに保存
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(save_path)
    
    return jsonify({
        "success": True, 
        "path": f"lefte_media/uploads/{filename}",
        "full_path": save_path
    })

# ダウンロード用（将来的にリンクをクリックした時に発動）
@app.route('/download/<path:filename>')
def download_from_hdd(filename):
    # 安全のため /mnt/hdd1/lefte_media 以下に限定
    return send_from_directory(HDD_BASE, filename, as_attachment=True)

if __name__ == '__main__':
    # 🚀 ここは一つだけでOK！
    socketio.start_background_task(background_monitor)
    
    cert_file = os.getenv("CERT_FILE")
    key_file = os.getenv("KEY_FILE")
    
    if cert_file and key_file and os.path.exists(cert_file):
        socketio.run(app, host="0.0.0.0", port=5000, 
                     certfile=cert_file, keyfile=key_file)
    else:
        socketio.run(app, host="0.0.0.0", port=5000)