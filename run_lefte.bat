@echo off
:: 【重要】コマンドプロンプトをUTF-8モードに切り替える呪文だよ
chcp 65001 >nul

title L.E.F.T.E. Unified Server
cd /d %~dp0

echo --------------------------------------------------
echo [1/3] 実行中の古いプロセスを掃除しています...
echo --------------------------------------------------
taskkill /f /im python.exe /t >nul 2>&1
timeout /t 2 /nobreak >nul

echo --------------------------------------------------
echo [2/3] レフティ（Port 5000）を起動しています...
echo --------------------------------------------------
echo.

:: 起動！
python lefte_server.py

pause