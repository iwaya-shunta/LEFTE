from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

# クライアント初期化
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("--- 利用可能なモデル一覧 ---")
for m in client.models.list():
    # モデル名と対応機能をシンプルに表示
    print(f"Name: {m.name}")
    # print(f"Supported actions: {m.supported_generation_methods}") # 詳細が必要な場合