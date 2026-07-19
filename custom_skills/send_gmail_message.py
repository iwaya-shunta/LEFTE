
"""
Gmailを使用して、指定された宛先にメールを送信します。件名と本文を指定可能です。既存の認証情報（token.json等）を使用して実行します。
"""
def send_gmail_message(*args, **kwargs):
    def send_gmail_message(to_email: str, subject: str, body: str) -> str:
        """
        Gmail APIを使用してメールを送信します。

        Args:
            to_email (str): 送信先のメールアドレス
            subject (str): メールの件名
            body (str): メールの本文
        """
        import os
        import base64
        from email.mime.text import MIMEText
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials

        # 認証情報の読み込み
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/gmail.send'])
    
        if not creds:
            return "認証情報が見つからないため、メールを送信できませんでした。"

        try:
            service = build('gmail', 'v1', credentials=creds)
            message = MIMEText(body)
            message['to'] = to_email
            message['subject'] = subject

            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            send_message = {'raw': raw}
        
            service.users().messages().send(userId="me", body=send_message).execute()
            return f"メール「{subject}」を {to_email} に送信したよ！"
        except Exception as e:
            return f"メール送信中にエラーが発生したよ: {str(e)}"
