Set fso = CreateObject("Scripting.FileSystemObject")
Set WshShell = CreateObject("WScript.Shell")
strPath = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.Run "pythonw """ & strPath & "\settings_menu.py""", 0, False
