
"""
VOICEVOX EngineのHTTP APIを直接叩いて、ユーザー辞書に単語を登録します。既存のライブラリの問題を回避します。
"""
def register_word_via_api(*args, **kwargs):
    import requests

    def register_word_via_api(surface: str, pronunciation: str, accent_type: int = 0) -> str:
        """
        VOICEVOX EngineのREST APIを使用して、ユーザー辞書に新しい単語を登録します。

        Args:
            surface: 漢字や言葉の表記（例: "駿太"）
            pronunciation: カタカナでの読み（例: "シュンタ"）
            accent_type: アクセント核の位置（デフォルト0）
        """
        url = "http://127.0.0.1:50021/user_dict_word"
        params = {
            "surface": surface,
            "pronunciation": pronunciation,
            "accent_type": accent_type
        }
    
        try:
            response = requests.post(url, params=params)
            if response.status_code == 200:
                return f"成功したよ！「{surface}（{pronunciation}）」を辞書に登録したよ！"
            else:
                return f"エラーが発生しちゃった...。ステータスコード: {response.status_code}, 内容: {response.text}"
        except Exception as e:
            return f"通信エラーが起きちゃったみたい：{str(e)}"

