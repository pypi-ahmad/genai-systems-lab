@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"
title GenAI Systems Lab Launcher

echo.
echo [GenAI Systems Lab] Checking prerequisites...

set "INSTALLED_PREREQUISITE="
set "MISSING_DOCKER="
set "MISSING_NODE="
where docker >nul 2>nul
if errorlevel 1 set "MISSING_DOCKER=1"
where node >nul 2>nul
if errorlevel 1 set "MISSING_NODE=1"

if defined MISSING_DOCKER goto :require_winget
if defined MISSING_NODE goto :require_winget
goto :install_prerequisites

:require_winget
where winget >nul 2>nul
if errorlevel 1 (
  echo ERROR: Windows Package Manager ^(winget^) is required to install missing prerequisites.
  echo Install or update "App Installer" from Microsoft Store, then run launch.cmd again.
  pause
  exit /b 1
)

:install_prerequisites
if defined MISSING_DOCKER (
  echo Docker Desktop is missing. Installing it through winget...
  winget install --exact --id Docker.DockerDesktop --accept-package-agreements --accept-source-agreements
  if errorlevel 1 goto :install_failed
  set "INSTALLED_PREREQUISITE=1"
)

if defined MISSING_NODE (
  echo Node.js LTS is missing. Installing it through winget...
  winget install --exact --id OpenJS.NodeJS.LTS --accept-package-agreements --accept-source-agreements
  if errorlevel 1 goto :install_failed
  set "INSTALLED_PREREQUISITE=1"
)

if defined INSTALLED_PREREQUISITE (
  echo.
  echo Prerequisites were installed. Windows may request UAC approval, WSL setup, or a restart.
  echo Complete any Docker Desktop setup, then run this same launch.cmd again.
  pause
  exit /b 0
)

echo Checking Docker Desktop...
docker info >nul 2>nul
if errorlevel 1 (
  if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" (
    start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
  )
  echo Waiting for the Docker engine to become ready...
  for /L %%I in (1,1,90) do (
    docker info >nul 2>nul
    if not errorlevel 1 goto :docker_ready
    timeout /t 2 /nobreak >nul
  )
  echo ERROR: Docker Desktop did not become ready within three minutes.
  echo Open Docker Desktop, complete any WSL or restart prompts, and rerun launch.cmd.
  pause
  exit /b 1
)

:docker_ready
if not exist ".data" mkdir ".data"

if not exist ".data\launcher.env" (
  echo Creating a persistent local encryption key...
  powershell -NoProfile -ExecutionPolicy Bypass -Command "$bytes = New-Object byte[] 32; $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create(); try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }; $key = [Convert]::ToBase64String($bytes).Replace('+','-').Replace('/','_'); Set-Content -LiteralPath '.data\launcher.env' -Value ('GENAI_SYSTEMS_LAB_BYOK_ENCRYPTION_KEY=' + $key) -Encoding Ascii"
  if errorlevel 1 (
    echo ERROR: Could not create .data\launcher.env.
    pause
    exit /b 1
  )
)

set "API_CONTAINER="
for /f "usebackq delims=" %%I in (`docker compose ps --status running -q api 2^>nul`) do set "API_CONTAINER=%%I"
if not defined API_CONTAINER (
  powershell -NoProfile -Command "if (Get-NetTCPConnection -State Listen -LocalPort 8514 -ErrorAction SilentlyContinue) { exit 42 }"
  if errorlevel 42 (
    echo ERROR: Port 8514 is already occupied by a process outside this Docker Compose API.
    echo Stop that process yourself or change its port, then rerun launch.cmd. Nothing was terminated.
    pause
    exit /b 1
  )
)

set "FRONTEND_ALREADY_RUNNING="
powershell -NoProfile -Command "if (Get-NetTCPConnection -State Listen -LocalPort 8513 -ErrorAction SilentlyContinue) { try { $page = Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8513/' -TimeoutSec 5; if ($page.Content -match 'GenAI Systems Lab') { exit 10 } } catch {}; exit 42 }"
if errorlevel 42 (
  echo ERROR: Port 8513 is occupied by another application.
  echo Stop that process yourself or change its port, then rerun launch.cmd. Nothing was terminated.
  pause
  exit /b 1
)
if errorlevel 10 set "FRONTEND_ALREADY_RUNNING=1"

echo Building and starting Postgres, Redis, API, and worker...
docker compose --env-file ".data\launcher.env" up -d --build postgres redis api worker
if errorlevel 1 (
  echo ERROR: Docker Compose could not start the backend stack.
  echo Review the error above and run launch.cmd again after correcting it.
  pause
  exit /b 1
)

echo Waiting for backend health...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$deadline = (Get-Date).AddMinutes(3); do { try { $response = Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8514/health' -TimeoutSec 3; if ($response.StatusCode -eq 200) { exit 0 } } catch {}; Start-Sleep -Seconds 2 } while ((Get-Date) -lt $deadline); exit 1"
if errorlevel 1 (
  echo ERROR: The backend did not become healthy. Run: docker compose logs api worker
  pause
  exit /b 1
)

if not defined FRONTEND_ALREADY_RUNNING (
  echo Installing frontend dependencies...
  pushd "portfolio"
  call npm install --no-audit --no-fund
  if errorlevel 1 (
    popd
    echo ERROR: npm could not install the frontend dependencies.
    pause
    exit /b 1
  )
  popd

  echo Starting the frontend...
  start "GenAI Systems Lab frontend" /min cmd /d /s /c "cd /d ""%~dp0portfolio"" && npm run dev ^> ""%~dp0.data\frontend.log"" 2^>^&1"
)

echo Waiting for frontend readiness...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$deadline = (Get-Date).AddMinutes(2); do { try { $response = Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8513/' -TimeoutSec 3; if ($response.StatusCode -eq 200 -and $response.Content -match 'GenAI Systems Lab') { exit 0 } } catch {}; Start-Sleep -Seconds 2 } while ((Get-Date) -lt $deadline); exit 1"
if errorlevel 1 (
  echo ERROR: The frontend did not become ready. Review .data\frontend.log.
  pause
  exit /b 1
)

echo Opening GenAI Systems Lab...
start "" "http://localhost:8513"
echo Ready. Backend: http://localhost:8514  Frontend: http://localhost:8513
exit /b 0

:install_failed
echo ERROR: winget could not install a required prerequisite.
echo Review the installer output, resolve the issue, and rerun launch.cmd.
pause
exit /b 1
