@echo off
echo ====================================================================
echo Starting CICADA OBSERVE Platform (Backend, Frontend, Collector)
echo ====================================================================

start "Cicada Backend (Port 8000)" cmd /k "cd /d %~dp0\..\backend && python run.py"
timeout /t 3 /nobreak >nul

start "Cicada Frontend (Port 3000)" cmd /k "cd /d %~dp0\..\frontend && npm run dev"
timeout /t 3 /nobreak >nul

start "Cicada Local Collector" cmd /k "cd /d %~dp0\..\collector && python run.py"

echo All services launched!
echo - Frontend: http://localhost:3000
echo - Backend:  http://127.0.0.1:8000 (Docs: http://127.0.0.1:8000/docs)
echo - Collector: Live background telemetry daemon
pause

