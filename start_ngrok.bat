@echo off
cd /d "%~dp0"
echo [Attendance] Starting ngrok tunnel for port 8000...
ngrok http 8000 --log=stdout > "%~dp0ngrok.log" 2>&1
