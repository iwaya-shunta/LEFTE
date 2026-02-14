import os

def list_photos():
    """Lists all the photos that have been uploaded.

    Returns:
        A list of URLs for the uploaded photos, or a message if no photos are found.
    """
    upload_dir = os.path.join('static', 'uploads')
    if not os.path.exists(upload_dir):
        return "写真アップロード用のディレクトリがまだ作成されていません。"

    try:
        files = os.listdir(upload_dir)
        photo_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]

        if not photo_files:
            return "まだ写真はありません。"

        # 各写真のURLを改行で区切った文字列を返す
        base_url = "/uploads"
        photo_urls = [f"{base_url}/{filename}" for filename in photo_files]
        
        return "アップロード済みの写真一覧:\n" + "\n".join(photo_urls)
    except Exception as e:
        return f"写真一覧の取得中にエラーが発生しました: {e}"
