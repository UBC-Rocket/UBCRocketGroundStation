@ECHO OFF


del .\dist\Station.exe
pyinstaller -F -n Station .\comWindow.py

xcopy .\comWindow.ui .\dist\ /y
xcopy .\main.ui .\dist\ /y


PAUSE