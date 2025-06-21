@echo off
echo [1/3] Activeer Python 3.11 virtuele omgeving...
call .venv311\Scripts\activate.bat

echo [2/3] Controleer Python versie...
python --version

echo [3/3] Installeer requirements...
pip install -r requirements.txt

echo.
echo Als je Python 3.11.x hierboven ziet, is de activering gelukt.
echo Je kunt nu je applicatie starten met:
echo cd services/realtime-voice ^&^& python -m uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
echo.

cd C:\Users\ahmet\Documents\doosletters_app\ai-voice-agent-v3
