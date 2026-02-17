import os
from datetime import datetime

STORAGE_PATH = '/mnt/hdd1/lefte_media'

def list_hdd_contents(directory_path: str):
    """
    HDD内の指定されたディレクトリにあるファイルやフォルダの一覧を詳細情報付きで返します。

    Args:
        directory_path (str): 読み取りたいディレクトリのパス。ルートを見る場合は "." を指定してください。
    """
    # 🚀 Gemini が空文字（''）を送ってきた時のための保険
    if not directory_path or directory_path == "''" or directory_path == "":
        directory_path = "."

    target = os.path.normpath(os.path.join(STORAGE_PATH, directory_path))
    
    # セキュリティ：指定範囲外へのアクセス禁止
    if not target.startswith(STORAGE_PATH):
        return "Error: アクセスが許可されていない領域です。"

    try:
        if not os.path.exists(target):
            return f"Error: '{directory_path}' は見つかりませんでした。"

        items = os.listdir(target)
        details = []
        for item in items:
            path = os.path.join(target, item)
            stats = os.stat(path)
            # 時刻を短くして Gemini の読み取り負担を減らす
            mtime = datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M')
            is_dir = "[DIR]" if os.path.isdir(path) else "[FILE]"
            size = f"{stats.st_size / 1024:.1f} KB" if not os.path.isdir(path) else "-"
            details.append(f"{is_dir} {item} (Size: {size}, Updated: {mtime})")
        
        return "\n".join(details) if details else "このフォルダは空です。"
    except Exception as e:
        return f"Error: {str(e)}"

def read_hdd_text_file(file_path: str):
    """
    HDD内のテキストファイルの内容を読み取ります。

    Args:
        file_path (str): 読み取りたいファイルのパス。
    """
    target = os.path.normpath(os.path.join(STORAGE_PATH, file_path))
    if not target.startswith(STORAGE_PATH):
        return "Error: アクセス権限がありません。"

    try:
        with open(target, 'r', encoding='utf-8') as f:
            # 長すぎるとGeminiのトークンを圧迫するので、先頭4000文字程度に制限
            return f.read(4000)
    except Exception as e:
        return f"Error: {str(e)}"