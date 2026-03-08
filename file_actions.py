# file_actions.py
import os

STORAGE_PATH = '/mnt/hdd1/lefte_media'

def create_local_file(filename: str, content: str):
    """
    指定されたファイル名（拡張子含む）と内容で、ファイルをHDDに生成・保存します。
    
    Args:
        filename (str): 作成するファイル名（例: 'test.py', 'memo.txt', 'index.html'）
        content (str): ファイルの中に書き込むテキスト内容
    """
    # セキュリティのため、保存先を制限
    target_path = os.path.join(STORAGE_PATH, filename)
    
    try:
        # ディレクトリがない場合は作成
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return f"✅ ファイル '{filename}' を作成して保存したよ！場所は {target_path} だよ。"
    except Exception as e:
        return f"❌ ファイル作成に失敗しちゃった: {str(e)}"