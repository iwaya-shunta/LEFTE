import chat_storage
from datetime import datetime

def save_note(content: str, date: str = None):
    """Saves or appends a note for a specific date. If no date is provided, today's date is used.

    Args:
        content: The text to add to the note.
        date: The date of the note in YYYY-MM-DD format. If not provided, defaults to today.

    Returns:
        A string confirming the result (saved, appended, or duplicate).
    """
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')

    try:
        status = chat_storage.save_note(date, content)
        if status == 'duplicate':
            return f"そのメモ「{content}」は{date}に既に存在します。"
        elif status in ['created', 'appended']:
            return f"メモを{date}に保存しました。"
        else:
            # 万が一、予期せぬステータスが返ってきた場合
            return "メモの保存中に不明な状態が発生しました。"
    except Exception as e:
        # In a real scenario, you might want to log the error more robustly
        return f"メモの保存中にエラーが発生しました: {e}"

def read_note(date: str = None):
    """Reads a note from a specific date. If no date is provided, today's date is used.

    Args:
        date: The date of the note to read in YYYY-MM-DD format.

    Returns:
        The content of the note or a message if not found.
    """
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    
    try:
        note_content = chat_storage.get_note(date)
        if note_content:
            return f"{date}のメモ:\n{note_content}"
        else:
            return f"{date}にはメモがありません。"
    except Exception as e:
        return f"メモの読み込み中にエラーが発生しました: {e}"
