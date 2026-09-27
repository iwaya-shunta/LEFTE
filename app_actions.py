# app_actions.py
import sqlite3
import os
import googlemaps

maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
gmaps = googlemaps.Client(key=maps_api_key) if maps_api_key else None

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

def search_nearby_places(
    latitude: float, longitude: float, keyword: str
) -> list[dict]:
    """指定された座標の周辺にある店舗や施設を検索します。

    Args:
        latitude: 現在地の緯度
        longitude: 現在地の経度
        keyword: 検索キーワード (例: 'コンビニ', 'カフェ', 'ラーメン')
    """
    if not gmaps:
        return [{"error": "GOOGLE_MAPS_API_KEY が設定されていません。"}]

    try:
        # 半径1.5km以内の施設を検索
        response = gmaps.places_nearby(
            location=(latitude, longitude),
            radius=1500,
            keyword=keyword,
            language="ja",
        )
        places = []
        for p in response.get("results", [])[:5]:
            places.append(
                {
                    "name": p.get("name"),
                    "vicinity": p.get("vicinity"),
                    "rating": p.get("rating"),
                    "total_ratings": p.get("user_ratings_total"),
                }
            )
        return places if places else [{"result": "該当する場所が見つかりませんでした。"}]
    except Exception as e:
        return [{"error": f"検索処理中にエラーが発生しました: {str(e)}"}]

init_apps_table()