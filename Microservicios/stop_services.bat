@echo off
setlocal enabledelayedexpansion
cd /d %~dp0

echo [Heartguard] Stopping services...
docker-compose down
endlocal
