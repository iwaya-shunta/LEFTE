import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from config import SCOPES  # 👈 さっき作った config.py から読み込むよ


def generate_token():
    # credentials.json（Google Cloudからダウンロードしたやつ）が必要だよ！
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)

    # 新しい token.json を保存！
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
    print("✨ token.json が正常に作成されました！ ✨")


if __name__ == "__main__":
    generate_token()