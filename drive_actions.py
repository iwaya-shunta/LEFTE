import io
import os
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from config import SCOPES
def get_drive_service():
    """Google Drive API への接続を確立します。"""
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        return build('drive', 'v3', credentials=creds)
    return None


def list_drive_files(folder_id: str = 'root', max_results: int = 10):
    """
    指定されたフォルダ（デフォルトはマイドライブのルート）内のファイル一覧を取得します。
    folder_id: アクセスしたいフォルダのID。マイドライブ直下なら 'root' を指定。
    """
    service = get_drive_service()
    if not service: return "ドライブの認証ができていないみたい。"

    results = service.files().list(
        q=f"'{folder_id}' in parents and trashed = false",
        pageSize=max_results,
        fields="nextPageToken, files(id, name, mimeType)"
    ).execute()

    items = results.get('files', [])
    if not items: return "ファイルは見つからなかったよ。"

    res = [f"ID: {i['id']} | 名前: {i['name']} | タイプ: {i['mimeType']}" for i in items]
    return "\n".join(res)


def search_drive_file(filename: str):
    service = get_drive_service()
    if not service: return "認証エラーだよ。"

    # 'contains' を使うことで、一部が合っていれば見つけられるようにする
    query = f"name contains '{filename}' and trashed = false"

    results = service.files().list(
        q=query,
        pageSize=10,
        fields="files(id, name, mimeType)"
    ).execute()

    items = results.get('files', [])
    if not items: return f"'{filename}' という名前のファイルは見つからなかったよ。"

    res = [f"ID: {i['id']} | 名前: {i['name']}" for i in items]
    return "\n".join(res)

def read_drive_file_content(file_id: str):
    """
    指定されたファイルの内容を読み取ります。
    Googleドキュメントの場合はテキストとしてエクスポートし、
    テキストファイルの場合はそのまま読み込みます。
    """
    service = get_drive_service()
    if not service: return "認証エラーだよ。"

    try:
        # ファイルの情報を取得して、種類（MIMEタイプ）を調べるよ
        file_metadata = service.files().get(fileId=file_id, fields='name, mimeType').execute()
        mime_type = file_metadata.get('mimeType')

        if mime_type == 'application/vnd.google-apps.document':
            # Google ドキュメントなら、テキスト形式で書き出す（エクスポート）よ
            request = service.files().export_media(fileId=file_id, mimeType='text/plain')
        else:
            # 普通のテキストファイルなら、そのままダウンロードするよ
            request = service.files().get_media(fileId=file_id)

        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()

        return fh.getvalue().decode('utf-8')

    except Exception as e:
        return f"ファイルを読むのに失敗しちゃった。エラー: {str(e)}"