import os, re, time, logging, base64, hashlib, asyncio, wave, io
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from flask_socketio import SocketIO, emit

# 🚀 VOICEVOX CORE のインポート
import requests
import voicevox_core

import chat_storage, hdd_actions, calendar_actions, drive_actions, search_actions, gmail_actions, app_actions, notes_actions, photo_actions
from lefte_brain import lefte_agent

load_dotenv()
app = Flask(__name__, static_url_path='', static_folder='static')
CORS(app)

# --- パス設定 ---
HDD_BASE = '/mnt/hdd1/lefte_media'
VOICE_DIR = os.path.join(HDD_BASE, 'voices')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DICT_DIR = "/home/iwaya/LEFTE/open_jtalk_dic_utf_8-1.11"
# voicevox_actions.py 内のパスも絶対パスに！
USER_DICT_PATH = "/home/iwaya/LEFTE/user_dict.json"
VOICE_LIB_DIR = "/home/iwaya/LEFTE/static/voices/library"
os.makedirs(VOICE_DIR, exist_ok=True)

# --- ログ設定 ---
LOG_FILE = os.path.join(HDD_BASE, 'lefte_system.log')
log_format = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler = RotatingFileHandler(LOG_FILE, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
file_handler.setFormatter(log_format)
logging.getLogger().addHandler(file_handler)
logging.getLogger().setLevel(logging.INFO)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

voice_library = {}
if os.path.exists(VOICE_LIB_DIR):
    for f in os.listdir(VOICE_LIB_DIR):
        if f.endswith(".wav"):
            word = f.replace(".wav", "")
            voice_library[word] = os.path.join(VOICE_LIB_DIR, f)

def get_silence(duration_sec, params):
    num_frames = int(params.framerate * duration_sec)
    return b'\x00' * (num_frames * params.sampwidth * params.nchannels)

def init_local_voice():
    global vv_synthesizer
    logging.info("🎤 ローカルVOICEVOX（春日部つむぎ）を初期化中...")
    
    try:
        from voicevox_core.blocking import Onnxruntime, OpenJtalk, Synthesizer, VoiceModelFile
        
        # 1. 心臓 (ONNX) の準備
        onnxruntime = Onnxruntime.load_once()

        # 2. 知識 (OpenJtalk) の準備
        # 成功実績のあるパスを指定してください
        open_jtalk = OpenJtalk(str(DICT_DIR))
        
        # 3. 身体 (Synthesizer) の構築
        vv_synthesizer = Synthesizer(onnxruntime, open_jtalk)
        
        # 4. 🚀 魂 (0.vvm: つむぎちゃん) のロード
        # つむぎちゃんが含まれている 0.vvm のフルパス
        model_file_path = "/home/iwaya/LEFTE/voicevox_core_runtime/voicevox_core/models/vvms/0.vvm"
        
        # 🚀 修正：絶対パスで指定
        user_dict_path = "/home/iwaya/LEFTE/user_dict.json"
        
        if os.path.exists(user_dict_path):
            try:
                from voicevox_core.blocking import UserDict
                u_dict = UserDict()
                u_dict.load(user_dict_path)
                
                # 🚀 Synthesizer ではなく、その中の open_jtalk に対して辞書を設定する
                if hasattr(vv_synthesizer.open_jtalk, "use_user_dict"):
                    vv_synthesizer.open_jtalk.use_user_dict(u_dict)
                    logging.info(f"📚 OpenJtalk 経由でユーザー辞書をロードしました")
                else:
                    logging.error("❌ open_jtalk オブジェクトにも use_user_dict が見当たりません")
                    
            except Exception as e:
                logging.error(f"❌ ユーザー辞書のロード失敗: {e}")

        logging.info(f"👤 つむぎちゃんの魂をロード中: {model_file_path}")
        voice_model = VoiceModelFile.open(model_file_path)
        vv_synthesizer.load_voice_model(voice_model)

        # 🚀 スタイルID 8 (春日部つむぎ ノーマル) を有効化
        # 0.16.4 ではこの直後に tts が可能になります
        
        logging.info("✅ VOICEVOXローカルエンジンの準備完了！（春日部つむぎ）")
        
    except Exception as e:
        import traceback
        logging.error(f"❌ 初期化失敗:\n{traceback.format_exc()}")

# def generate_voice(text, speaker_id=8):
#     """
#     【先制再生ハイブリッド】
#     文頭の数語をライブラリから取得し、残りをVOICEVOXで一括生成して滑らかに繋ぐ
#     """
#     # --- 1. テキストの徹底クリーニング ---
#     # 読み上げない部分（感情表現、制御タグ、記号）を除去
#     text_for_query = re.sub(r'\(.*?\)|（.*?）', '', text)
#     text_for_query = re.sub(r'\[.*?\]', '', text_for_query)
#     text_for_query = re.sub(r'[^\w\s、。！？ーっ]', '', text_for_query)
    
#     if not text_for_query.strip():
#         text_for_query = "了解だよ。"

#     # キャッシュ（同じ文章なら即返却）
#     file_hash = hashlib.md5(text.encode()).hexdigest()
#     cache_path = os.path.join(VOICE_DIR, f"{file_hash}.wav")
#     if os.path.exists(cache_path): return cache_path

#     logging.info(f"🎤 生成開始（ハイブリッド）: {text_for_query}")

#     try:
#         # --- 2. 文頭の切り出し（先鋒パーツ探し） ---
#         # 読み（かな）を取得してパース
#         query_check = vv_synthesizer.create_audio_query(text_for_query, speaker_id)
#         kana_full = query_check.kana.replace("/", "").replace("'", "").replace("_", "")

#         first_part = None
#         remaining_kana = kana_full

#         # よく使う出だしパーツ（長い順）
#         # これがライブラリ（116個）にあれば、それを出だしとして採用
#         starters = ["オツカレサマ", "コンニチハ", "レフティー", "シュンタ", "ボク", "エヘヘ"]
#         for s in starters:
#             if kana_full.startswith(s):
#                 first_part = s
#                 remaining_kana = kana_full[len(s):]
#                 break

#         # --- 3. 音声データの準備 ---
#         parts_to_combine = []
        
#         # A: 出だしがライブラリにあれば採用
#         if first_part and first_part in voice_library:
#             parts_to_combine.append(voice_library[first_part])
#             logging.info(f"⚡ 文頭をライブラリから採用: {first_part}")
#         else:
#             # 文頭が見つからなければ、全体をVOICEVOXに任せるのでここは空のまま次へ
#             remaining_kana = kana_full

#         # B: 残りの全文章を一括生成（これによりイントネーションが滑らかになる）
#         if remaining_kana.strip():
#             logging.info(f"🎨 本文を一括生成中: {remaining_kana}")
#             q = vv_synthesizer.create_audio_query(remaining_kana, speaker_id)
#             # 連結時の継ぎ目を自然にするための調整
#             q.pre_phoneme_length = 0.05
#             q.post_phoneme_length = 0.05
#             main_wav = vv_synthesizer.synthesis(q, speaker_id)
#             parts_to_combine.append(io.BytesIO(main_wav))

#         # --- 4. 物理連結（waveモジュール） ---
#         combined_data = []
#         params = None
#         for source in parts_to_combine:
#             with wave.open(source, 'rb') as w:
#                 if params is None:
#                     params = w.getparams()
#                 combined_data.append(w.readframes(w.getnframes()))

#         if not combined_data or params is None:
#             # 最終フォールバック：何もできなかったら全文を普通に生成
#             return generate_voice_legacy(text, speaker_id)

#         # 書き出し
#         with wave.open(cache_path, 'wb') as output:
#             output.setparams(params)
#             for data in combined_data:
#                 output.writeframes(data)

#         logging.info(f"✅ 完成: {len(parts_to_combine)}つの塊を連結")
#         return cache_path

#     except Exception as e:
#         logging.error(f"Hybrid Engine Error: {e}")
#         return None

def generate_voice(text, speaker_id=8):
    """バックアップ用：純粋なVOICEVOX一括生成"""
    file_hash = hashlib.md5(text.encode()).hexdigest()
    path = os.path.join(VOICE_DIR, f"{file_hash}.wav")
    # クリーニング後のテキストで生成
    clean = re.sub(r'\(.*?\)|（.*?）|\[.*?\]|[^\w\s、。！？ーっ]', '', text)
    q = vv_synthesizer.create_audio_query(clean, speaker_id)
    wav = vv_synthesizer.synthesis(q, speaker_id)
    with open(path, "wb") as f: f.write(wav)
    return path

# (以下、SocketIO処理やルーティングは変更なし)
@socketio.on('chat_request')
def handle_chat(data):
    emit('ai_thinking', broadcast=True)
    socketio.start_background_task(process_chat_task, data)

def process_chat_task(data):
    user_input = data.get('message', '')
    image_url = data.get('image_url')
    try:
        chat_storage.save_message('user', user_input, image_url)
        result = lefte_agent.run(user_input)
        full_text = result.output or "完了だよ。"
        chat_storage.save_message('assistant', full_text)
        socketio.emit('chat_update', {"user_message": user_input, "response": full_text, "voice_url": None, "image_url": image_url})
        def async_voice(text):
            path = generate_voice(text)
            if path:
                fn = os.path.basename(path)
                socketio.emit('voice_ready', {"voice_url": f"/wav_files/{fn}"})
        socketio.start_background_task(async_voice, full_text)
    except Exception as e:
        logging.error(f"Chat error: {e}")
        socketio.emit('error_message', {"response": str(e)})

@app.route('/')
def index(): return send_file(os.path.join(BASE_DIR, 'desktpo.html'))

@app.route('/history', methods=['GET'])
def history_api():
    rows = chat_storage.get_today_history()
    return jsonify([{"timestamp": r[0], "role": r[1], "content": r[2], "image_url": r[3]} for r in rows])

@app.route('/wav_files/<filename>')
def serve_wav(filename): return send_from_directory(VOICE_DIR, filename)

@app.route('/get_news', methods=['GET'])
def get_news():
    try:
        # GoogleニュースのRSSを取得してJSONに変換するサービスを利用
        rss_url = "https://news.google.com/rss?hl=ja&gl=JP&ceid=JP:ja"
        res = requests.get(f"https://api.rss2json.com/v1/api.json?rss_url={rss_url}")
        return jsonify({"news": res.json().get('items', [])})
    except Exception as e:
        logging.error(f"News error: {e}")
        return jsonify({"news": [], "error": str(e)})

@app.route('/launch_app', methods=['POST'])
def launch_app_api():
    data = request.json
    app_path = data.get('path')
    try:
        if os.path.exists(app_path):
            os.startfile(os.path.normpath(app_path))
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "パスが見つからないよ"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/uploads/<filename>')
def serve_upload(filename):
    # アップロードした画像などを表示するために必要です
    UPLOAD_FOLDER = os.path.join(HDD_BASE, 'uploads')
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    init_local_voice()
    cert_file = os.getenv("CERT_FILE")
    key_file = os.getenv("KEY_FILE")
    if cert_file and key_file and os.path.exists(cert_file) and os.path.exists(key_file):
        socketio.run(app, host="0.0.0.0", port=5000, certfile=cert_file, keyfile=key_file)
    else:
        socketio.run(app, host="0.0.0.0", port=5000)