# lefte_brain.py
import os, logging
from google import genai
from google.genai import types
from datetime import datetime
from dotenv import load_dotenv
import importlib
import glob

# 各種アクションのインポート
import calendar_actions, gmail_actions, drive_actions, search_actions, app_actions, hdd_actions, notes_actions, photo_actions, file_actions, developer_actions



load_dotenv()

def load_custom_skills():
    dynamic_tools = []
    # custom_skills フォルダが存在しない場合は作成
    if not os.path.exists("custom_skills"):
        os.makedirs("custom_skills")
        
    skill_files = glob.glob("custom_skills/*.py")
    for file in skill_files:
        try:
            module_name = os.path.basename(file)[:-3]
            spec = importlib.util.spec_from_file_location(module_name, file)
            module = importlib.util.module_from_spec(spec)
            # 🚀 ここでエラーが起きても catch して次に進む
            spec.loader.exec_module(module)
            func = getattr(module, module_name)
            dynamic_tools.append(func)
            print(f"✅ スキル読み込み成功: {module_name}")
        except Exception as e:
            # エラーが起きたスキルだけを無視して、サーバーは起動し続ける
            print(f"⚠️ スキル『{file}』は文法エラーのためスキップしました: {e}")
    return dynamic_tools

# --- ツール（関数）のリスト ---
tools = [
    calendar_actions.list_calendar_events,
    calendar_actions.add_calendar_event,
    gmail_actions.list_recent_emails,
    search_actions.search_web,
    app_actions.launch_app,
    hdd_actions.list_hdd_contents,
    notes_actions.save_note,
    notes_actions.read_note,
    photo_actions.list_photos,
    file_actions.create_local_file,
    drive_actions.list_drive_files,
    drive_actions.search_drive_file,
    drive_actions.read_drive_file_content,
    developer_actions.develop_new_skill,
]+ load_custom_skills()



class LefteAgent:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key)
        
        # 🚀 モデルを gemini-3-flash-preview に固定
        self.model_id = "gemini-3-flash-preview"
        
        # システム指示の取得
        self.instruction = self._get_system_instruction()
        
        # 🚀 OpenClaw化の核心: チャットセッションの作成
        # これにより、AIは「ツール実行 → 失敗 → 別の方法で再試行」というループを内部で回せます
        self.chat_session = self.client.chats.create(
            model=self.model_id,
            config=types.GenerateContentConfig(
                system_instruction=self.instruction,
                tools=tools,
                # 自動関数呼び出しをON。AIが「もう一度別のツールを呼ぶべきだ」と判断したら自動実行されます
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
            )
        )

    def _get_system_instruction(self):
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(BASE_DIR, "personality.txt")
        personality = open(path, "r", encoding="utf-8").read() if os.path.exists(path) else "あなたは助手の L.E.F.T.E. です。"
        
        # 🚀 OpenClaw風の「あきらめない」指示を追加
        agent_rules = """
        【自律実行ルール】
        1. ツール実行が失敗（Error）を返した場合、すぐに諦めてユーザーに報告しないでください。
        2. 失敗の原因を分析し、引数を変えるか、別のツール（例：検索やファイル一覧確認）を組み合わせて再試行してください。
        3. ユーザーの目的を達成するために、必要であれば複数のツールを連続して使用してください。
        4. 最終的な結果だけを、あなたの性格（レフティ）に合わせて報告してください。
        """
        return f"{personality}\n{agent_rules}"

    def run(self, user_input):
        # 現在時刻を付与（時間認識の修正）
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        full_prompt = f"【現在時刻: {current_time}】\n{user_input}"
        
        logging.info(f"🤖 Agent (gemini-3) 思考開始: {user_input[:30]}...")

        try:
            # 🚀 session.send_message を使うことで、これまでの文脈を維持した試行錯誤が可能
            response = self.chat_session.send_message(full_prompt)
            
            # OpenClawの戻り値形式に合わせるためのラップクラス
            class Result:
                def __init__(self, text):
                    self.output = text
            
            return Result(response.text or "ごめんね、うまく答えが見つからなかったよ。")
            
        except Exception as e:
            logging.error(f"❌ Agent Error: {e}")
            raise e

# 実体の作成
lefte_agent = LefteAgent()