@echo off
setlocal

set "ROOT=%~dp0"

echo Demarrage des serveurs...
echo.

start "Backend Flask" cmd /k ""cd /d "%ROOT%backend" && python -m pip install -r requirements.txt && python run.py""
start "Frontend Vue" cmd /k ""cd /d "%ROOT%frontend" && npm install && npm run dev""

echo Backend lance dans une fenetre "Backend Flask".
echo Frontend lance dans une fenetre "Frontend Vue".
echo.
echo Ouvre ensuite http://localhost:5173

endlocal
