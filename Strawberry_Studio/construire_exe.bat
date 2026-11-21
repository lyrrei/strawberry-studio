@echo off
chcp 65001 >nul
py -m pip install -r requirements.txt
py -m PyInstaller --noconfirm --clean --onefile --windowed --name StrawberryStudio --add-data "overlay.html;." --hidden-import websocket --hidden-import obsws_python app.py
echo.
echo Si la compilation reussit, le fichier est dans dist\StrawberryStudio.exe
pause
