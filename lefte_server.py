import os, re, requests, time, logging, base64
from logging.handlers import RotatingFileHandler
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, emit
from google import genai
from google.genai import types

# 自作アクションの読み込み
import chat_storage, hdd_actions, calendar_actions, drive_actions, search_actions, gmail_actions, app_actions, notes_actions, photo_actions

load_dotenv()
app = Flask(__name__, static_url_path='', static_folder='static')
CORS(app)

# --- パス設定 ---
VOICEVOX_URL = os.getenv("VOICEVOX_URL", "http://127.0.0.1:50021")
HDD_BASE = '/mnt/hdd1/lefte_media'
VOICE_DIR = os.path.join(HDD_BASE, 'voices')
os.makedirs(VOICE_DIR, exist_ok=True)
UPLOAD_FOLDER = os.path.join(HDD_BASE, 'uploads')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

for d in [VOICE_DIR, UPLOAD_FOLDER]: os.makedirs(d, exist_ok=True)

# --- ログ設定 ---
LOG_FILE = os.path.join(HDD_BASE, 'lefte_system.log')
log_format = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler = RotatingFileHandler(LOG_FILE, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
file_handler.setFormatter(log_format)
logging.getLogger().addHandler(file_handler)
logging.getLogger().setLevel(logging.INFO)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
chat_storage.init_db()

# --- ツール一覧 ---
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

FUNCTIONAL_RULES = """
1. カレンダー/ドライブ等は当然の日常として使い、説明は不要。
2. 簡潔に回答せよ。
3. アプリを起動する際は、ツールが返した '🚀LAUNCH_SIGNAL:...' を必ず含めること。
4. ツール実行に失敗した場合は、技術的なエラーログを出すのではなく、ユーザーに「何ができなかったか」を1行で伝える。
5. 音声合成（Voicevox）で読み上げるため、URLや複雑な記号、メタデータは本文に含めない。
6. ユーザーを「しゅんた」と認識し、適度な距離感のアシスタントとして振る舞う。
"""

def get_system_instruction():
    personality_path = os.path.join(BASE_DIR, "personality.txt")
    if os.path.exists(personality_path):
        with open(personality_path, "r", encoding="utf-8") as f:
            personality = f.read()
    else:
        personality = "あなたは助手の L.E.F.T.E. です。"
    return f"{personality}\n{FUNCTIONAL_RULES}"

# --- 音声生成 (Voicevox) ---
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
        logging.error(f"Voice generation error: {e}")

# --- ルーティング ---
@app.route('/')
def index():
    return send_file(os.path.join(BASE_DIR, 'desktpo.html'))

@app.route('/history', methods=['GET'])
def history_api():
    rows = chat_storage.get_today_history()
    return jsonify([{"role": r[1], "content": r[2], "image_url": r[3]} for r in rows])

@app.route('/uploads/<filename>')
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/wav_files/<filename>')
def serve_wav(filename):
    return send_from_directory(VOICE_DIR, filename)

@app.route('/upload_to_hdd', methods=['POST'])
def upload_to_hdd():
    file = request.files.get('file')
    if not file or file.filename == '':
        return jsonify({"success": False, "error": "No file"}), 400
    # 🚀 修正：拡張子をしっかり取り出し、ドットを維持する
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        ext = '.jpg' # 不明な場合は jpg に固定
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}{ext}" # 例: 20260217_231500.jpg
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(save_path)
    logging.info(f"💾 HDD保存完了: {filename}")
    return jsonify({
        "success": True, 
        "path": f"uploads/{filename}"
    })

# --- WebSocket 処理 ---
@socketio.on('chat_request')
def handle_chat(data):
    emit('ai_thinking', broadcast=True)
    socketio.start_background_task(process_chat_task, data)

def process_chat_task(data):
    user_input = data.get('message', '')
    image_b64 = data.get('image') # Socket.IO経由のデータ
    image_url = data.get('image_url') # HDD上のパス
    mime_type = data.get('mime_type')
    model_name = data.get('model', 'gemini-3-flash-preview')

    try:
        chat_storage.save_message('user', user_input, image_url)
        past_rows = chat_storage.get_today_history()
        
        contents = []
        # 1. 履歴の構築
        for r in past_rows[-11:-1]:
            role = "user" if r[1] == "user" else "model"
            parts = [{"text": r[2]}]
            if r[3]: # image_url
                full_path = os.path.join(HDD_BASE, r[3]) # 🚀 修正：replaceは不要
                if os.path.exists(full_path):
                    with open(full_path, "rb") as f:
                        encoded = base64.b64encode(f.read()).decode('utf-8')
                        mtype = "image/png" if r[3].endswith('.png') else "image/jpeg"
                        parts.append({"inline_data": {"data": encoded, "mime_type": mtype}})
            contents.append({"role": role, "parts": parts})

        # 2. 今回の入力を構築
        user_parts = [{"text": f"【現在時刻: {datetime.now().strftime('%H:%M:%S')}】\n{user_input}"}]
        
        # 🚀 Socket経由で画像が届かず、HDDパスがある場合はHDDから読み込む
        final_image_b64 = image_b64
        if not final_image_b64 and image_url:
            full_path = os.path.join(HDD_BASE, image_url)
            if os.path.exists(full_path):
                with open(full_path, "rb") as f:
                    final_image_b64 = base64.b64encode(f.read()).decode('utf-8')

        if final_image_b64 and mime_type:
            user_parts.append({"inline_data": {"data": final_image_b64, "mime_type": mime_type}})
        
        contents.append({"role": "user", "parts": user_parts})

        # 4. Gemini API 呼び出し
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
        chat_storage.save_message('assistant', full_text)

        # 5. 音声生成とUI更新
        voice_filename = f"v_{int(time.time())}.wav"
        generate_voice(full_text, filename=os.path.join(VOICE_DIR, voice_filename))

        socketio.emit('chat_update', {
            "user_message": user_input, 
            "response": full_text, 
            "voice_url": f"/wav_files/{voice_filename}",
            "image_url": image_url
        })

    except Exception as e:
        logging.error(f"Chat error: {e}")
        socketio.emit('error_message', {"response": str(e)})

def background_monitor():
    while True:
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = int(f.read()) / 1000.0
            socketio.emit('sys_status', {'cpu_temp': f"{temp:.1f}"})
        except: pass
        socketio.sleep(5)

# lefte_server.py に追加
@app.route('/get_news', methods=['GET'])
def get_news():
    try:
        # GoogleニュースのRSSを取得してJSONに変換してくれる無料サービスを利用
        rss_url = "https://news.google.com/rss?hl=ja&gl=JP&ceid=JP:ja"
        res = requests.get(f"https://api.rss2json.com/v1/api.json?rss_url={rss_url}")
        return jsonify({"news": res.json().get('items', [])})
    except Exception as e:
        return jsonify({"news": [], "error": str(e)})

# lefte_server.py に追加
@app.route('/launch_app', methods=['POST'])
def launch_app_api():
    data = request.json
    app_path = data.get('path')
    try:
        if os.path.exists(app_path):
            os.startfile(os.path.normpath(app_path)) # 🚀 Windowsアプリを起動！
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "パスが見つからないよ"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
# --- 🚀 起動処理 (SSL対応) ---

if __name__ == '__main__':
    socketio.start_background_task(background_monitor)
    
    cert_file = os.getenv("CERT_FILE")
    key_file = os.getenv("KEY_FILE")
    
    # 証明書とキーの両方が存在する場合のみ SSL モードで起動
    if cert_file and key_file and os.path.exists(cert_file) and os.path.exists(key_file):
        logging.info("🔐 SSLモード (HTTPS) で起動します")
        socketio.run(app, host="0.0.0.0", port=5000, 
                     certfile=cert_file, keyfile=key_file)
    else:
        logging.warning("⚠️ 証明書が見つからないため、通常モード (HTTP) で起動します")
        socketio.run(app, host="0.0.0.0", port=5000)