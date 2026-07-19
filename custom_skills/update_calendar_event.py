
"""
Googleカレンダーの既存の予定（時間や件名など）を更新します。
"""
def update_calendar_event(*args, **kwargs):
    import os.path
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    def update_calendar_event(event_id: str, summary: str = None, start_time: str = None, end_time: str = None, description: str = None) -> str:
        """
        Googleカレンダーの既存の予定を更新します。
    
        Args:
            event_id: 更新する予定のID。
            summary: 予定の件名。
            start_time: 開始時刻 (ISO 8601形式: YYYY-MM-DDTHH:MM:SS+09:00)。
            end_time: 終了時刻 (ISO 8601形式: YYYY-MM-DDTHH:MM:SS+09:00)。
            description: 予定の詳細な説明。
        """
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        # 既存のトークンファイルを使用
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        service = build('calendar', 'v3', credentials=creds)
    
        # 現在の予定を取得
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
    
        # 変更がある場合のみ上書き
        if summary:
            event['summary'] = summary
        if start_time:
            event['start'] = {'dateTime': start_time, 'timeZone': 'Asia/Tokyo'}
        if end_time:
            event['end'] = {'dateTime': end_time, 'timeZone': 'Asia/Tokyo'}
        if description:
            event['description'] = description
        
        updated_event = service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
        return f"予定を更新しました！: {updated_event.get('htmlLink')}"

