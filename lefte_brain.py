# lefte_brain.py
import os, logging
from google import genai
from google.genai import types
from datetime import datetime
from dotenv import load_dotenv
import importlib
import glob
import chat_storage

# 各種アクションのインポート
import calendar_actions, gmail_actions, drive_actions, search_actions, app_actions, hdd_actions, notes_actions, photo_actions, file_actions, developer_actions, voicevox_actions

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
    voicevox_actions.register_word,
]+ load_custom_skills()



class LefteAgent:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key)
        
        # 🚀 モデルを gemini-3-flash-preview に固定
        self.model_id = "gemini-3-flash-preview"
        
        # システム指示の取得
        self.instruction = self._get_system_instruction()
        
        # 過去の履歴を読み込む (デフォルト30日)
        self.history = self._load_recent_history()
        
        # 🚀 OpenClaw化の核心: チャットセッションの作成
        # これにより、AIは「ツール実行 → 失敗 → 別の方法で再試行」というループを内部で回せます
        self.chat_session = self.client.chats.create(
            model=self.model_id,
            config=types.GenerateContentConfig(
                system_instruction=self.instruction,
                tools=tools,
                # 自動関数呼び出しをON。AIが「もう一度別のツールを呼ぶべきだ」と判断したら自動実行されます
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
            ),
            history=self.history
        )

    def _load_recent_history(self, days=30):
        """データベースから過去30日分の履歴を読み込み、Geminiのhistory形式に変換する"""
        history_data = chat_storage.get_history_by_days(days)
        formatted_history = []
        
        # 履歴が多すぎるとトークン数制限に引っかかるか、処理に時間がかかる可能性があるので、
        # 直近の1000件までに制限するなどの対策を入れておく
        if len(history_data) > 1000:
            history_data = history_data[-1000:]
            
        # Geminiのhistoryは user -> model -> user -> model の交互である必要があるため、
        # 連続する同一ロールのメッセージは結合する
        for row in history_data:
            timestamp, role, content, image_url = row
            # roleが'system'など予期しないものの場合はスキップするかuser扱いにする
            gemini_role = "model" if role == "assistant" or role == "model" else "user"
            
            if not content:
                continue
                
            text_part = f"[{timestamp}] {content}"
            
            if formatted_history and formatted_history[-1].role == gemini_role:
                # 前のメッセージと同じロールの場合は、テキストを追加（改行して結合）
                existing_text = formatted_history[-1].parts[0].text
                formatted_history[-1].parts = [types.Part.from_text(text=f"{existing_text}\n{text_part}")]
            else:
                # 異なるロール（または初回）の場合は新規追加
                formatted_history.append(
                    types.Content(
                        role=gemini_role,
                        parts=[types.Part.from_text(text=text_part)]
                    )
                )
                
        # historyは最初のメッセージが "user" である必要がある
        if formatted_history and formatted_history[0].role != "user":
            formatted_history.pop(0)

        # 念のため末尾がuserだった場合はGemini APIがエラーを吐く可能性があるので、
        # 今回はhistoryとして渡すだけなので問題ないケースも多いが、
        # 厳密な user->model->user->model を要求される。
        # historyを渡すときは偶数件(最後の要素がmodel)である必要がある場合が多い。
        if formatted_history and formatted_history[-1].role == "user":
            formatted_history.pop() # ★末尾のユーザー発言を削って、Modelで終わるように（もしくは空になるように）変更

        # --- ここから追加: 完全な交互チェックと強制修正 ---
        validated_history = []
        expected_role = "user"
        for msg in formatted_history:
            if msg.role == expected_role:
                validated_history.append(msg)
                expected_role = "model" if expected_role == "user" else "user"
            else:
                logging.warning(f"履歴の順序が不正です。期待されるロール: {expected_role}, 実際のロール: {msg.role}。結合済みですが無視します。")

        if validated_history and validated_history[-1].role == "user":
            validated_history.pop()

        logging.info(f"📚 {days}日分の履歴（{len(validated_history)}件）を読み込みました。")
        return validated_history

    def _get_system_instruction(self):
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(BASE_DIR, "personality.txt")
        personality = open(path, "r", encoding="utf-8").read() if os.path.exists(path) else "あなたは助手の L.E.F.T.E. です。"
        
        # 🚀 緩急タグの使い分け指示を追加
        tempo_rules = """
        【発話ガイドライン】
        あなたは人間味のある対話を行うため、以下のタグを文章の中に挿入して、自分の話速を自由にコントロールしてください。
        - [slow] : 感情を込める言葉、強調したい重要事項、考え込むような場面。
        - [fast] : 勢いのある相槌、さらっと流す補足説明、興奮している時。
        - [normal]: 丁寧な説明や、通常の会話。
        
        例：「[slow]駿太、[normal]今日もお疲れ様！[fast]ランニングの記録をまとめておいたよ！」

        会話の中に、ボクっ娘らしい可愛くてユーモアのある顔文字や絵文字を積極的に混ぜてね！例：(๑•̀ㅂ•́)و✧、✨、( ´艸｀)、🚀
        """
        
        agent_rules = """
        【自律実行ルール】
        （以前の自律実行ルールをここに記述...）
        """
        return f"{personality}\n{tempo_rules}\n{agent_rules}"

    def run(self, user_input, media_path=None, mime_type=None):
        # 現在時刻を付与（時間認識の修正）
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        full_prompt = f"【現在時刻: {current_time}】\n{user_input}"
        
        logging.info(f"🤖 Agent (gemini-3) 思考開始: {user_input[:30]}...")

        try:
            content_parts = [full_prompt]
            
            if media_path and os.path.exists(media_path):
                logging.info(f"📂 メディアファイルを検知: {media_path}")
                # 🚀 google-genai の仕様に合わせて、mime_type ではなく config の中で指定するか、単にパスを渡す
                uploaded_file = self.client.files.upload(file=media_path)
                
                # 動画ファイルの処理中は完了を待つ
                if uploaded_file.state.name == "PROCESSING":
                    import time
                    logging.info("⏳ 動画の処理完了を待機中...")
                    while uploaded_file.state.name == "PROCESSING":
                        time.sleep(2)
                        uploaded_file = self.client.files.get(name=uploaded_file.name)
                        
                content_parts.insert(0, uploaded_file) # テキストの前にファイルを配置
            
            # session.send_message を使うことで、これまでの文脈を維持した試行錯誤が可能
            response = self.chat_session.send_message(content_parts)
            
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