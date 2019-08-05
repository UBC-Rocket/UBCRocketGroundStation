@ECHO OFF


del .\dist\Station.exe
.\venv\Scripts\pyinstaller.exe -F -n Station .\comWindow.py

xcopy .\comWindow.ui .\dist\ /y
xcopy .\main.ui .\dist\ /y
xcopy .\marker.png .\dist\ /y
xcopy .\tiles\* .\dist\tiles\ /e /i /y


PAUSE