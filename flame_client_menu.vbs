Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
strPath = fso.GetParentFolderName(WScript.ScriptFullName)
q = Chr(34)

' Try specific Python path first (from user environment)
pythonPath = "C:\Python314\pythonw.exe"

pythonConsolePath = "C:\Python314\python.exe"

If Not fso.FileExists(pythonPath) Then
    ' Fallback to system PATH
    pythonPath = "pythonw"
End If

If Not fso.FileExists(pythonConsolePath) Then
    pythonConsolePath = "python"
End If

' If pythonw isn't available, fall back to python (visible console)
If pythonPath = "pythonw" And Not fso.FileExists("C:\\Python314\\pythonw.exe") Then
    pythonPath = pythonConsolePath
End If

' Run the settings menu (hidden if pythonw) and capture errors to a log file
logPath = strPath & "\launcher.log"
cmd = "cmd /c " & q & q & pythonPath & q & " " & q & strPath & "\settings_menu.py" & q & " >> " & q & logPath & q & " 2>&1" & q
WshShell.Run cmd, 0, False
