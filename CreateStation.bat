@ECHO OFF


del .\dist\Station.exe
pyinstaller -F -n Station .\comWindow.py


PAUSE