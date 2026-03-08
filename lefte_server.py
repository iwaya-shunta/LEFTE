import os, re, requests, time, logging, base64, hashlib
from logging.handlers import RotatingFileHandler
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, emit

# 自作アクションとストレージの読み込み
import chat_storage, hdd_actions, calendar_actions, drive_actions, search_actions, gmail_actions, app_actions, notes_actions, photo_actions
from lefte_brain import lefte_agent

load_dotenv()
app = Flask(__name__, static_url_path='', static_folder='static')
CORS(app)

# --- パス設定 ---#
#VOICEVOX_URL = os.getenv("VOICEVOX_URL", "http://127.0.0.1:50021")
VOICEVOX_WEB_API_URL = os.getenv("VOICEVOX_WEB_API_URL", "https://api.tts.quest/v2/voicevox/audio")
SU_SHIKI_API_KEY = os.getenv("SU_SHIKI_API_KEY", "")
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

# 🚀 eventlet を使用して非同期処理を安定させる
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')
chat_storage.init_db()

def generate_voice(text, speaker_id=8):
    # 1. テキストの洗浄（記号除去とカッコ内削除）
    # 読み上げを自然にするための処理
    clean_text = re.sub(r'#+\s*|[*_~-]|`|>', '', text)
    clean_text = re.sub(r'\(.*?\)|（.*?）', '', clean_text)
    clean_text = clean_text.replace('\n', ' ')
    
    if not clean_text.strip(): 
        clean_text = "了解だよ。"

    # 🚀 【限界を拡張】POSTを使うので、500文字くらいまで余裕で喋れます！
    # あまりに長すぎると今度は音声生成に時間がかかりすぎるので、500文字程度が快適です
    MAX_CHARS = 500 
    if len(clean_text) > MAX_CHARS:
        clean_text = clean_text[:MAX_CHARS] + "。 長くなっちゃうから、続きは画面を見てね！"

    # 2. キャッシュ確認
    file_hash = hashlib.md5(clean_text.encode()).hexdigest()
    cache_path = os.path.join(VOICE_DIR, f"{file_hash}.wav")

    if os.path.exists(cache_path):
        return cache_path

    try:
        api_key = os.getenv("SU_SHIKI_API_KEY", "L98808u96_61112")
        # 🚀 動作確認済みのドメイン
        base_url = "https://deprecatedapis.tts.quest/v2/voicevox/audio/"
        
        # パラメータ設定
        payload = {
            'key': api_key,
            'speaker': speaker_id,
            'pitch': 0,
            'intonationScale': 1.4,
            'speed': 1.15,
            'text': clean_text
        }

        # 🚀 【ここがポイント！】 get ではなく post を使います
        # data=payload とすることで、テキストがURLの外側を通って送られます
        res = requests.post(base_url, data=payload, timeout=60)
        
        # デバッグ用ログ：実際にどんなURLを叩いたか（POSTなのでURLは短いままのはず）
        logging.info(f"🔗 POSTリクエスト送信完了 (文字数: {len(clean_text)})")

        if res.status_code != 200:
            logging.error(f"❌ APIエラー ({res.status_code}): {res.text}")
            return None

        # 3. 保存
        with open(cache_path, "wb") as f:
            f.write(res.content)
        
        return cache_path

    except Exception as e:
        logging.error(f"Voice generation error: {e}")
        return None

# --- ルーティング ---
@app.route('/')
def index():
    return send_file(os.path.join(BASE_DIR, 'desktpo.html'))

@app.route('/history', methods=['GET'])
def history_api():
    rows = chat_storage.get_today_history()
    return jsonify([{"timestamp": r[0], "role": r[1], "content": r[2], "image_url": r[3]} for r in rows])

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
    ext = os.path.splitext(file.filename)[1].lower()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}{ext}"
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(save_path)
    return jsonify({"success": True, "path": f"uploads/{filename}"})

@app.route('/get_news', methods=['GET'])
def get_news():
    try:
        rss_url = "https://news.google.com/rss?hl=ja&gl=JP&ceid=JP:ja"
        res = requests.get(f"https://api.rss2json.com/v1/api.json?rss_url={rss_url}")
        return jsonify({"news": res.json().get('items', [])})
    except: return jsonify({"news": []})

# --- WebSocket 処理 ---
@socketio.on('chat_request')
def handle_chat(data):
    emit('ai_thinking', broadcast=True)
    socketio.start_background_task(process_chat_task, data)

def process_chat_task(data):
    user_input = data.get('message', '')
    image_url = data.get('image_url')
    
    try:
        chat_storage.save_message('user', user_input, image_url)
        
        # 1. 脳（エージェント）に考えさせる
        logging.info(f"🤖 思考中: {user_input}")
        result = lefte_agent.run(user_input)
        full_text = result.output or "完了だよ。"
        
        # 2. 🚀 【重要】まずテキストだけを即座にUIへ返信！
        chat_storage.save_message('assistant', full_text)
        socketio.emit('chat_update', {
            "user_message": user_input, 
            "response": full_text, 
            "voice_url": None, # ここではまだ音声は送らない
            "image_url": image_url
        })

        # 3. 🚀 【重要】バックグラウンドで音声を生成し、できたら追加で送る
        def async_voice_generation(text):
            voice_path = generate_voice(text)
            if voice_path:
                voice_fn = os.path.basename(voice_path)
                # 音声の準備ができたことを個別に通知
                socketio.emit('voice_ready', {
                    "voice_url": f"/wav_files/{voice_fn}"
                })
        
        # 生成を別タスクで実行
        socketio.start_background_task(async_voice_generation, full_text)

    except Exception as e:
        logging.error(f"🤖 LEFTE Agent Error: {e}")
        socketio.emit('error_message', {"response": f"ごめんね、ちょっと手間取っちゃった：{str(e)}"})

def background_monitor():
    while True:
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = int(f.read()) / 1000.0
            socketio.emit('sys_status', {'cpu_temp': f"{temp:.1f}"})
        except: pass
        socketio.sleep(5)

if __name__ == '__main__':
    socketio.start_background_task(background_monitor)
    cert_file, key_file = os.getenv("CERT_FILE"), os.getenv("KEY_FILE")
    if cert_file and key_file and os.path.exists(cert_file) and os.path.exists(key_file):
        socketio.run(app, host="0.0.0.0", port=5000, certfile=cert_file, keyfile=key_file)
    else:
        socketio.run(app, host="0.0.0.0", port=5000)