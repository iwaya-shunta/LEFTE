"""
Gmailからメール一覧を取得したり、本文を読み取ったりします。
"""
import base64
import os
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from config import SCOPES

def gmail_reader(action: str = 'list', message_id: str = None, max_results: int = 5):
    """
    Gmailから最新のメール一覧（IDと件名）を取得したり、特定のメッセージIDを指定して本文を読み取ったりします。

    Args:
        action: 'list'（一覧取得）または 'read'（本文取得）を指定してください。
        message_id: 'read'アクションの時に使用するメッセージID（任意）。
        max_results: 'list'アクションの時に取得する件数（デフォルト5）。
    """
    token_path = 'token.json'
    if not os.path.exists(token_path):
        return "エラー: token.jsonが見つかりません。認証を先に済ませてください。"

    try:
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        service = build('gmail', 'v1', credentials=creds)

        if action == 'list':
            results = service.users().messages().list(userId='me', maxResults=max_results).execute()
            messages = results.get('messages', [])
            if not messages:
                return "メールは見つかりませんでした。"

            output = []
            for msg in messages:
                m = service.users().messages().get(userId='me', id=msg['id'], format='metadata').execute()
                headers = m.get('payload', {}).get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                output.append(f"ID: {msg['id']} | 件名: {subject}")
            return "\n".join(output)

        elif action == 'read':
            if not message_id:
                return "エラー: message_idを指定してください。"
            
            message = service.users().messages().get(userId='me', id=message_id, format='full').execute()
            payload = message.get('payload', {})
            parts = payload.get('parts', [])
            body = ""

            if not parts:
                data = payload.get('body', {}).get('data', '')
                if data: body = base64.urlsafe_b64decode(data).decode('utf-8')
            else:
                for part in parts:
                    if part['mimeType'] == 'text/plain':
                        data = part.get('body', {}).get('data', '')
                        if data: body = base64.urlsafe_b64decode(data).decode('utf-8')
            
            return f"【本文】:\n{body[:1500]}" # 1500文字で制限

    except Exception as e:
        return f"エラーが発生しました: {str(e)}"