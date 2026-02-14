import sqlite3
import os

db_path = 'chat_history.db'

print(f"--- データベース確認 ---")
if not os.path.exists(db_path):
    print(f"❌ ファイル '{db_path}' が見当たりません！")
    print(f"現在の作業ディレクトリ: {os.getcwd()}")
else:
    print(f"✅ ファイルが見つかりました（サイズ: {os.path.getsize(db_path)} bytes）")

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # テーブルの一覧を確認
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = c.fetchall()
    print(f"テーブル一覧: {tables}")

    # メッセージの件数を確認
    c.execute("SELECT COUNT(*) FROM messages")
    count = c.fetchone()[0]
    print(f"保存されているメッセージ件数: {count} 件")

    # 直近5件を表示
    if count > 0:
        print("\n--- 直近5件のデータ ---")
        c.execute("SELECT id, timestamp, role, content FROM messages ORDER BY id DESC LIMIT 5")
        for row in c.fetchall():
            print(f"ID:{row[0]} | {row[1]} | {row[2]}: {row[3][:20]}...")

    conn.close()