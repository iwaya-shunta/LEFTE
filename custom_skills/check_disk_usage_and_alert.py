"""
指定されたパスのディスク使用量をチェックし、使用率が閾値を超えていたら警告します。
"""
import shutil

def check_disk_usage_and_alert(path: str = "/", threshold: int = 90):
    """
    ディスクの使用状況を確認して、空き容量が少ない場合に警告を返します。

    Args:
        path: チェックしたいディレクトリのパス (例: "/")
        threshold: 警告を出す使用率のしきい値 (%) (例: 90)
    """
    try:
        total, used, free = shutil.disk_usage(path)
        percent_used = (used / total) * 100

        # ギガバイト換算
        total_gb = total / (1024**3)
        used_gb = used / (1024**3)
        free_gb = free / (1024**3)

        result = f"【ディスク診断結果】\n使用率: {percent_used:.1f}%\n空き容量: {free_gb:.1f} GB"

        if percent_used > threshold:
            return "⚠️警告⚠️ " + result + f"\n使用率が{threshold}%を超えているよ！"
        else:
            return "✅正常✅ " + result + "\n余裕があるから、まだ大丈夫そうだね。"

    except Exception as e:
        return f"エラーが発生しちゃったみたい：{str(e)}"

