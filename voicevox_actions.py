# voicevox_actions.py
import os
import logging
# 🚀 修正：インポートの仕方を変更します
from voicevox_core.blocking import UserDict
from voicevox_core import UserDictWord

# 辞書ファイルの保存場所（絶対パス）
USER_DICT_PATH = "/home/iwaya/LEFTE/user_dict.json"

def register_word(surface: str, pronunciation: str, accent_type: int = 0):
    """
    VOICEVOXのユーザー辞書に新しい単語を登録します。
    
    Args:
        surface: 漢字や言葉の表記（例: "駿太"）
        pronunciation: カタカナでの読み（例: "シュンタ"）
        accent_type: アクセント核の位置（デフォルト0）
    """
    try:
        # 1. 既存の辞書を読み込むか新規作成
        user_dict = UserDict()
        if os.path.exists(USER_DICT_PATH):
            user_dict.load(USER_DICT_PATH)
        
        # 2. 🚀 ここが修正ポイント：UserDictWord を直接使う
        word = UserDictWord(surface, pronunciation, accent_type=accent_type)
        user_dict.add_word(word)
        
        # 3. ファイルに保存（永続化）
        user_dict.save(USER_DICT_PATH)
        
        # 4. 実行中のエンジンに反映（OpenJTalk側に適用）
        from lefte_server import vv_synthesizer
        if vv_synthesizer:
            vv_synthesizer.open_jtalk.use_user_dict(user_dict)
            
        return f"✅ 辞書に登録したよ！『{surface}』はこれから『{pronunciation}』って読むね！"
    except Exception as e:
        # ログにも詳細を残す
        logging.error(f"辞書登録エラー詳細: {e}")
        return f"❌ 辞書登録に失敗しちゃった: {e}"