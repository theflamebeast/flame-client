Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
strPath = fso.GetParentFolderName(WScript.ScriptFullName)

' Try specific Python path first (from user environment)
pythonPath = "C:\Python314\pythonw.exe"

If Not fso.FileExists(pythonPath) Then
    ' Fallback to system PATH
    pythonPath = "pythonw"
End If

' Run the settings menu hidden
WshShell.Run """" & pythonPath & """ """ & strPath & "\settings_menu.py""", 0, False
