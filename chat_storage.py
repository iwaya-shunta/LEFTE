import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, 'chat_history.db')

def init_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        # 🚀 image_url カラムを追加（既にテーブルがある場合は後述の ALTER 文が必要）
        c.execute('''CREATE TABLE IF NOT EXISTS messages
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      role TEXT,
                      content TEXT,
                      timestamp TEXT,
                      image_url TEXT)''') # 👈 ここを追加
        
        c.execute('''CREATE TABLE IF NOT EXISTS notes
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      date TEXT UNIQUE,
                      content TEXT)''')
        conn.commit()
        conn.close()
        print(f"✅ DB初期化完了: {DB_NAME}")
    except Exception as e:
        print(f"❌ DB初期化エラー: {e}")

def save_message(role, content, image_url=None): # 🚀 image_url を引数に追加
    if not content and not image_url: return # どちらも無い場合は保存しない
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 🚀 image_url も含めて INSERT する
        c.execute("INSERT INTO messages (role, content, timestamp, image_url) VALUES (?, ?, ?, ?)",
                  (role, content, now, image_url))
        conn.commit()
        conn.close()
        print(f"💾 Saved {role}: {content[:15]}... (Image: {image_url})")
    except Exception as e:
        print(f"❌ 保存エラー: {e}")

def get_today_history():
    """本日の履歴を取得（画像URLも含む）"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        today_str = datetime.now().strftime('%Y-%m-%d')

        # 🚀 image_url も SELECT の対象に含める
        # timestamp=r[0], role=r[1], content=r[2], image_url=r[3] になります
        c.execute('''SELECT timestamp, role, content, image_url FROM messages
                     WHERE timestamp LIKE ?
                     ORDER BY id ASC''', (f'{today_str}%',))

        rows = c.fetchall()

        if len(rows) == 0:
            c.execute('SELECT timestamp FROM messages ORDER BY id DESC LIMIT 1')
            last = c.fetchone()
            if last:
                print(f"⚠️ 検索失敗！形式不一致: DB内={last[0]}, 検索={today_str}")
        else:
            print(f"📂 履歴読込: {len(rows)}件取得成功！")

        conn.close()
        return rows
    except Exception as e:
        print(f"❌ 読込エラー: {e}")
        return []

# --- Note Functions (変更なし) ---
def save_note(date, content_to_add):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT content FROM notes WHERE date = ?", (date,))
        row = c.fetchone()
        status = ''
        if row:
            existing_content = row[0]
            if content_to_add in existing_content.split('\n'):
                status = 'duplicate'
            else:
                new_content = f"{existing_content}\n{content_to_add}"
                c.execute("UPDATE notes SET content = ? WHERE date = ?", (new_content, date))
                status = 'appended'
        else:
            c.execute("INSERT INTO notes (date, content) VALUES (?, ?)", (date, content_to_add))
            status = 'created'
        conn.commit()
        conn.close()
        return status
    except Exception as e:
        print(f"❌ Note saving error: {e}")
        raise e

def get_note(date):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT content FROM notes WHERE date = ?", (date,))
        row = c.fetchone()
        conn.close()
        return row[0] if row else None
    except Exception as e:
        print(f"❌ Note reading error: {e}")
        return None