# Windows PC上で実行するスクリプト (lefte_launcher.py)
import winreg
import sys
import os

def register_protocol():
    # 登録するプロトコル名
    protocol = "lefte-launch"
    # このスクリプト自身のパスを取得
    launcher_path = os.path.abspath(__file__)
    # 実行するコマンド（Pythonで自分自身を呼び出す）
    command = f'python "{launcher_path}" "%1"'

    try:
        # レジストリに書き込み（管理者権限が必要な場合があります）
        key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, protocol)
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "L.E.F.T.E. Launcher Protocol")
        winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
        
        shell_key = winreg.CreateKey(key, r"shell\open\command")
        winreg.SetValueEx(shell_key, "", 0, winreg.REG_SZ, command)
        
        print(f"✅ {protocol}:// プロトコルを登録しました！")
    except Exception as e:
        print(f"❌ エラー: {e}")

def main():
    if len(sys.argv) > 1:
        # プロトコル経由で渡された引数 (lefte-launch://パス) を解析
        raw_url = sys.argv[1]
        app_path = raw_url.replace("lefte-launch://", "").rstrip("/")
        # Windowsのパス形式に修正して起動
        os.startfile(os.path.normpath(app_path))
    else:
        register_protocol()

if __name__ == "__main__":
    main()