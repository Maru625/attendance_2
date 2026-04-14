@echo off
cd /d "%~dp0"
start "Attendance Server" cmd /k "cd /d "%~dp0" && start_server.bat"
start "Attendance ngrok" cmd /k "cd /d "%~dp0" && start_ngrok.bat"
