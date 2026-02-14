import os
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from config import SCOPES

def get_gmail_service():
    # 既存のカレンダー等と同じトークン（またはGmail権限を追加したもの）を使う
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    return build('gmail', 'v1', credentials=creds)


def list_recent_emails(max_results: int = 5):
    """
    最新の未読メールの件名をリストアップします。

    Args:
        max_results (int): 取得するメールの最大件数。
    """
    """最新の未読メールをリストアップする"""
    service = get_gmail_service()
    results = service.users().messages().list(userId='me', labelIds=['UNREAD'], maxResults=max_results).execute()
    messages = results.get('messages', [])

    email_list = []
    for msg in messages:
        m = service.users().messages().get(userId='me', id=msg['id']).execute()
        # 件名を取得
        headers = m['payload']['headers']
        subject = next(h['value'] for h in headers if h['name'] == 'Subject')
        email_list.append(subject)

    return email_list