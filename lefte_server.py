import os, re, requests, time, logging
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
    if not file: return jsonify({"success": False}), 400
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{secure_filename(file.filename)}"
    if filename.endswith('_'): filename += "image.jpg"
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(save_path)
    return jsonify({"success": True, "path": f"uploads/{filename}"})

# --- WebSocket 処理 ---
@socketio.on('chat_request')
def handle_chat(data):
    emit('ai_thinking', broadcast=True)
    socketio.start_background_task(process_chat_task, data)

def process_chat_task(data):
    user_input = data.get('message', '')
    image_b64 = data.get('image')
    image_url = data.get('image_url')
    mime_type = data.get('mime_type')
    
    try:
        chat_storage.save_message('user', user_input, image_url)
        past_rows = chat_storage.get_today_history()
        contents = [{"role": ("user" if r[1] == "user" else "model"), "parts": [{"text": r[2]}]} for r in past_rows[-11:-1]]
        
        user_parts = [{"text": f"【現在時刻: {datetime.now().strftime('%H:%M:%S')}】\n{user_input}"}]
        if image_b64 and mime_type:
            user_parts.append({"inline_data": {"data": image_b64, "mime_type": mime_type}})
        contents.append({"role": "user", "parts": user_parts})

        response = client.models.generate_content(
            model=data.get('model', 'gemini-3-flash-preview'),
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction="あなたはL.E.F.T.E.です。", 
                tools=tools, 
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
            )
        )
        full_text = response.text or "完了だよ。"
        chat_storage.save_message('assistant', full_text)

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