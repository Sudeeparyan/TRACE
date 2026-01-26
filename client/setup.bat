@echo off
echo Installing client dependencies...
call npm install

echo.
echo Installation complete!
echo.
echo To start the dashboard:
echo   1. Start the backend: start_server.bat
echo   2. Start the frontend: npm run dev
echo.
echo Or use mock data mode by setting VITE_USE_MOCK=true in .env
pause
