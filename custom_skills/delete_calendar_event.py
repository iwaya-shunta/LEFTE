
"""
Googleカレンダーから特定の予定を削除します。
"""
def delete_calendar_event(*args, **kwargs):
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    import os

    def delete_calendar_event(event_id: str):
        """
        Googleカレンダーから特定の予定を削除します。

        Args:
            event_id (str): 削除する予定のID。
        """
        if not os.path.exists('token.json'):
            return "Error: token.json not found."
    
        creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/calendar'])
        service = build('calendar', 'v3', credentials=creds)
    
        try:
            service.events().delete(calendarId='primary', eventId=event_id).execute()
            return f"予定（ID: {event_id}）を正常に削除しました。"
        except Exception as e:
            return f"予定の削除中にエラーが発生しました: {str(e)}"

