
"""
HDD上のテキストファイルの内容を読み取ります。
"""
def read_local_file(*args, **kwargs):
    import os

    def read_local_file(filepath: str) -> str:
        """
        HDD上のテキストファイルの内容を読み取ります。

        Args:
            filepath: 読み取りたいファイルのパス。
        """
        if not os.path.exists(filepath):
            return f"エラー: ファイル '{filepath}' が見つかりません。"
    
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except Exception as e:
            return f"エラー: ファイルの読み取りに失敗しました。{str(e)}"

