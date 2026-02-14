# app_actions.py
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, 'chat_history.db')

def init_apps_table():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS apps
                 (id INTEGER PRIMARY KEY, app_name TEXT UNIQUE, exe_path TEXT)''')
    conn.commit()
    conn.close()

def register_app(app_name: str, exe_path: str):
    init_apps_table()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO apps (app_name, exe_path) VALUES (?, ?)", (app_name, exe_path))
    conn.commit()
    conn.close()
    return f"了解だよ！『{app_name}』を登録したから、いつでも起動できるよ。"

def launch_app(app_name: str):
    """パスを直接送らず、DBに登録された名前だけをプロトコルに載せる"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT app_name FROM apps WHERE app_name = ?", (app_name,))
    row = c.fetchone()
    conn.close()
    if row:
        # 🚀 重要：パス(C:/...)ではなく名前(メモ帳)だけを投げる
        return f"🚀LAUNCH_SIGNAL:lefte-launch://{app_name}" # ここを修正
    return f"ごめんね、『{app_name}』はまだ登録されていないみたい。"

init_apps_table()