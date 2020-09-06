@ECHO OFF

cd /D %~dp0

IF EXIST .\venv\ (
echo Venv detected
) ELSE (
echo Creating Venv
python -m pip install --upgrade pip setuptools wheel
python -m venv venv
)

.\venv\scripts\python.exe -m pip install --upgrade pip setuptools
.\venv\scripts\python.exe -m pip install -r .\requirements.txt

del .\dist\Station.exe
.\venv\Scripts\pyinstaller.exe -F -n Station .\comWindow.py

xcopy .\qt_files\com_window.ui .\dist\qt_files\ /y
xcopy .\qt_files\main.ui .\dist\qt_files\ /y
xcopy .\qt_files\marker.png .\dist\qt_files\ /y


PAUSE