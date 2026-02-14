' --- start_hidden.vbs のおすすめ修正版 ---
Set ws = CreateObject("WScript.Shell")
' この VBS がある場所のフォルダパスを取得するよ
strPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)

' 絶対パスを書かずに、strPath を使って run_lefte.bat を呼び出す
ws.Run "cmd /c " & Chr(34) & strPath & "\run_lefte.bat" & Chr(34), 0, False

' VOICEVOX は多くの人が同じ場所にインストールするからそのままでも OK だよ
ws.run "cmd /c " & Chr(34) & "C:\Program Files\VOICEVOX\vv-engine\run.exe" & Chr(34), 0

Set ws = Nothing