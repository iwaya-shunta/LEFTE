import sqlite3

# データベースに接続
conn = sqlite3.connect('chat_history.db')
c = conn.cursor()

# --- 会話履歴の表示 ---
c.execute("SELECT timestamp, role, content FROM messages ORDER BY id ASC")
rows = c.fetchall()

print(f"--- 履歴データ全 {len(rows)} 件 ---")
for row in rows:
    print(f"[{row[0]}] {row[1]}: {row[2][:80]}...") # 長い場合は省略して表示
print("\n" + "="*30 + "\n") # 区切り線

# --- メモの表示 ---
try:
    c.execute("SELECT date, content FROM notes ORDER BY date DESC")
    note_rows = c.fetchall()

    print(f"--- メモデータ全 {len(note_rows)} 件 ---")
    if not note_rows:
        print("（メモはまだありません）")
    else:
        for row in note_rows:
            print(f"[{row[0]}]")
            # メモの内容をインデントして表示
            for line in row[1].split('\n'):
                print(f"  - {line}")
            print("-" * 20) # メモごとの区切り
except sqlite3.OperationalError:
    print("--- メモデータ ---")
    print("（notesテーブルがまだ作成されていません）")


conn.close()