import datetime
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os
from config import SCOPES

def get_calendar_service():
    """Google Calendar API への接続を確立します。"""
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        return build('calendar', 'v3', credentials=creds)
    return None


def list_calendar_events(max_results: int = 10):
    """
    Googleカレンダーから直近の予定を取得します。
    max_results: 取得する予定の最大件数（整数で指定してください）。
    """
    service = get_calendar_service()
    if not service:
        return "カレンダーの認証ができていないみたい。token.json を確認してね。"

    # 現在時刻をUTCで取得
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    events_result = service.events().list(
        calendarId='primary',
        timeMin=now,
        maxResults=max_results,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])
    if not events:
        return "予定は何も見つからなかったよ！今は暇なのかな？"

    # AIが読み取りやすいテキスト形式に変換するよ
    results = []
    for e in events:
        start = e['start'].get('dateTime', e['start'].get('date'))
        results.append(f"ID: {e['id']} | 件名: {e['summary']} | 開始: {start}")

    return "\n".join(results)


def add_calendar_event(summary: str, start_time: str, end_time: str, description: str = ""):
    """
    新しい予定をカレンダーに追加します。
    summary: 予定の件名
    start_time: 開始時刻 (ISO 8601形式: YYYY-MM-DDTHH:MM:SS+09:00)
    end_time: 終了時刻 (ISO 8601形式: YYYY-MM-DDTHH:MM:SS+09:00)
    description: 予定の詳細な説明（任意）
    """
    service = get_calendar_service()
    if not service: return "認証エラーだよ。"

    event = {
        'summary': summary,
        'description': description,
        'start': {'dateTime': start_time, 'timeZone': 'Asia/Tokyo'},
        'end': {'dateTime': end_time, 'timeZone': 'Asia/Tokyo'},
    }
    result = service.events().insert(calendarId='primary', body=event).execute()
    return f"予定「{summary}」を追加したよ！ URL: {result.get('htmlLink')}"


def delete_calendar_event(event_id: str):
    """
    指定された ID を持つ予定を削除します。
    event_id: 削除したい予定の固有ID（list_calendar_events で確認したもの）。
    """
    service = get_calendar_service()
    if not service: return "認証エラー。"

    service.events().delete(calendarId='primary', eventId=event_id).execute()
    return f"ID: {event_id} の予定を削除したよ。スッキリしたね！"


def update_calendar_event(event_id: str, summary: str = None, start_time: str = None, end_time: str = None):
    """
    既存の予定の内容を更新します。
    event_id: 更新したい予定の固有ID。
    summary: 新しい件名（変更する場合のみ指定）
    start_time: 新しい開始時刻（変更する場合のみ指定）
    end_time: 新しい終了時刻（変更する場合のみ指定）
    """
    service = get_calendar_service()
    if not service: return "認証エラー。"

    event = service.events().get(calendarId='primary', eventId=event_id).execute()
    if summary: event['summary'] = summary
    if start_time: event['start']['dateTime'] = start_time
    if end_time: event['end']['dateTime'] = end_time

    result = service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
    return f"予定を更新したよ！新しい件名は「{result.get('summary')}」だね。"