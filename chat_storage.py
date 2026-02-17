import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, 'chat_history.db')

def init_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        # image_url カラムを追加
        c.execute('''CREATE TABLE IF NOT EXISTS messages
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      role TEXT,
                      content TEXT,
                      timestamp TEXT,
                      image_url TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS notes
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      date TEXT UNIQUE,
                      content TEXT)''')
        conn.commit()
        conn.close()
        print(f"✅ DB初期化完了: {DB_NAME}")
    except Exception as e:
        print(f"❌ DB初期化エラー: {e}")

def save_message(role, content, image_url=None):
    if not content and not image_url: return
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # image_url も一緒に保存
        c.execute("INSERT INTO messages (role, content, timestamp, image_url) VALUES (?, ?, ?, ?)",
                  (role, content, now, image_url))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ 保存エラー: {e}")

def get_today_history():
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        today_str = datetime.now().strftime('%Y-%m-%d')
        c.execute('''SELECT timestamp, role, content, image_url FROM messages
                     WHERE timestamp LIKE ?
                     ORDER BY id ASC''', (f'{today_str}%',))
        rows = c.fetchall()
        conn.close()
        return rows
    except Exception as e:
        return []