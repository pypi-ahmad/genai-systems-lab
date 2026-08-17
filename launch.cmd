@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"
title GenAI Systems Lab Launcher

echo.
echo [GenAI Systems Lab] Launcher starting...

REM ─────────────────────────────────────────────────────────────────────────────
REM  MODE SELECTION
REM  Default: uv venv + direct uvicorn (no Docker required, simpler).
REM  Pass --docker to use Docker Compose instead.
REM ─────────────────────────────────────────────────────────────────────────────
set "USE_DOCKER="
if /i "%~1"=="--docker" set "USE_DOCKER=1"

if defined USE_DOCKER goto :docker_mode
goto :venv_mode

REM ═════════════════════════════════════════════════════════════════════════════
REM  UV VENV MODE  (default — first-time setup with uv, no Docker required)
REM ═════════════════════════════════════════════════════════════════════════════
:venv_mode
echo.
echo [GenAI Systems Lab] Mode: uv venv  (use --docker flag for Docker Compose mode)

REM ── uv ──────────────────────────────────────────────────────────────────────
where uv >nul 2>nul
if errorlevel 1 (
  echo uv not found — installing via pip...
  python -m pip install --quiet uv 2>nul
  if errorlevel 1 (
    echo uv not available via pip. Trying winget...
    where winget >nul 2>nul
    if errorlevel 1 (
      echo ERROR: Cannot install uv. Install it manually from https://docs.astral.sh/uv/
      pause
      exit /b 1
    )
    winget install --exact --id astral-sh.uv --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
      echo ERROR: winget could not install uv.
      pause
      exit /b 1
    )
  )
)

REM ── Python venv ──────────────────────────────────────────────────────────────
if not exist ".venv\" (
  echo Creating .venv in project root with uv...
  uv venv .venv
  if errorlevel 1 (
    echo ERROR: uv venv failed.
    pause
    exit /b 1
  )
)

echo Syncing Python dependencies with uv...
uv sync --all-extras
if errorlevel 1 (
  echo ERROR: uv sync failed. Check pyproject.toml and your Python installation.
  pause
  exit /b 1
)

REM ── .data directory and Fernet key ───────────────────────────────────────────
if not exist ".data" mkdir ".data"

if not exist ".data\launcher.env" (
  echo Generating persistent Fernet encryption key...
  .venv\Scripts\python.exe -c "from cryptography.fernet import Fernet; key=Fernet.generate_key().decode(); open('.data/launcher.env','w').write(f'GENAI_SYSTEMS_LAB_BYOK_ENCRYPTION_KEY={key}\n')" 2>nul
  if errorlevel 1 (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$bytes = New-Object byte[] 32; $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create(); try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }; $key = [Convert]::ToBase64String($bytes).Replace('+','-').Replace('/','_'); Set-Content -LiteralPath '.data\launcher.env' -Value ('GENAI_SYSTEMS_LAB_BYOK_ENCRYPTION_KEY=' + $key) -Encoding Ascii"
  )
)

REM ── .env file ────────────────────────────────────────────────────────────────
if not exist ".env" (
  echo Creating .env from .env.example...
  copy ".env.example" ".env" >nul
  echo Edit .env to set GENAI_SYSTEMS_LAB_JWT_SECRET for production use.
)

REM Load launcher key into env for this session
for /f "usebackq tokens=1,* delims==" %%A in (".data\launcher.env") do (
  set "%%A=%%B"
)

REM ── Port check ───────────────────────────────────────────────────────────────
set "BACKEND_RUNNING="
powershell -NoProfile -Command "if (Get-NetTCPConnection -State Listen -LocalPort 8514 -ErrorAction SilentlyContinue) { exit 10 }"
if errorlevel 10 set "BACKEND_RUNNING=1"

set "FRONTEND_RUNNING="
powershell -NoProfile -Command "if (Get-NetTCPConnection -State Listen -LocalPort 8513 -ErrorAction SilentlyContinue) { exit 10 }"
if errorlevel 10 set "FRONTEND_RUNNING=1"

REM ── Start backend ────────────────────────────────────────────────────────────
if not defined BACKEND_RUNNING (
  echo Starting FastAPI backend on port 8514...
  start "GenAI Systems Lab backend" /min cmd /d /s /c ".venv\Scripts\uvicorn.exe shared.api.app:app --host 0.0.0.0 --port 8514 > .data\backend.log 2>&1"
) else (
  echo Backend already running on port 8514 — skipping.
)

REM ── Wait for backend ─────────────────────────────────────────────────────────
echo Waiting for backend to become healthy...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$deadline = (Get-Date).AddSeconds(60); do { try { $r = Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8514/health' -TimeoutSec 3; if ($r.StatusCode -eq 200) { exit 0 } } catch {}; Start-Sleep -Seconds 2 } while ((Get-Date) -lt $deadline); exit 1"
if errorlevel 1 (
  echo ERROR: Backend did not become healthy. Review .data\backend.log
  pause
  exit /b 1
)
echo Backend is healthy.

REM ── Node.js check ────────────────────────────────────────────────────────────
where node >nul 2>nul
if errorlevel 1 (
  echo Node.js not found — skipping frontend.
  echo Install Node.js LTS from https://nodejs.org and re-run to get the UI.
  goto :open_api
)

REM ── Start frontend ────────────────────────────────────────────────────────────
if not defined FRONTEND_RUNNING (
  echo Installing frontend dependencies...
  pushd "portfolio"
  call npm install --no-audit --no-fund
  if errorlevel 1 (
    popd
    echo ERROR: npm could not install frontend dependencies.
    pause
    exit /b 1
  )
  popd

  echo Starting Next.js frontend on port 8513...
  start "GenAI Systems Lab frontend" /min cmd /d /s /c "cd /d ""%~dp0portfolio"" && npm run dev ^> ""%~dp0.data\frontend.log"" 2^>^&1"
) else (
  echo Frontend already running on port 8513 — skipping.
)

REM ── Wait for frontend ─────────────────────────────────────────────────────────
echo Waiting for frontend to become ready...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$deadline = (Get-Date).AddMinutes(2); do { try { $r = Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8513/' -TimeoutSec 3; if ($r.StatusCode -eq 200) { exit 0 } } catch {}; Start-Sleep -Seconds 2 } while ((Get-Date) -lt $deadline); exit 1"
if errorlevel 1 (
  echo WARNING: Frontend did not respond. Review .data\frontend.log
) else (
  start "" "http://localhost:8513"
  echo.
  echo Ready.
  echo   Frontend: http://localhost:8513
  echo   Backend:  http://localhost:8514
  echo   API docs: http://localhost:8514/docs
  exit /b 0
)

:open_api
start "" "http://localhost:8514/docs"
echo.
echo Ready. API at http://localhost:8514  (OpenAPI docs: http://localhost:8514/docs)
exit /b 0


REM ═════════════════════════════════════════════════════════════════════════════
REM  DOCKER MODE  (launch.cmd --docker)
REM ═════════════════════════════════════════════════════════════════════════════
:docker_mode
echo.
echo [GenAI Systems Lab] Mode: Docker Compose

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
  echo Install or update "App Installer" from Microsoft Store, then run launch.cmd --docker again.
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
  echo Prerequisites were installed. Complete any Docker Desktop setup, then run launch.cmd --docker again.
  pause
  exit /b 0
)

echo Checking Docker Desktop...
docker info >nul 2>nul
if errorlevel 1 (
  if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" (
    start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
  )
  echo Waiting for Docker engine...
  for /L %%I in (1,1,90) do (
    docker info >nul 2>nul
    if not errorlevel 1 goto :docker_ready
    timeout /t 2 /nobreak >nul
  )
  echo ERROR: Docker Desktop did not become ready. Run it manually and retry.
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
    echo Stop that process yourself, then rerun launch.cmd --docker.
    pause
    exit /b 1
  )
)

set "FRONTEND_ALREADY_RUNNING="
powershell -NoProfile -Command "if (Get-NetTCPConnection -State Listen -LocalPort 8513 -ErrorAction SilentlyContinue) { try { $page = Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8513/' -TimeoutSec 5; if ($page.Content -match 'GenAI Systems Lab') { exit 10 } } catch {}; exit 42 }"
if errorlevel 42 (
  echo ERROR: Port 8513 is occupied by another application.
  pause
  exit /b 1
)
if errorlevel 10 set "FRONTEND_ALREADY_RUNNING=1"

echo Building and starting Postgres, Redis, API, and worker...
docker compose --env-file ".data\launcher.env" up -d --build postgres redis api worker
if errorlevel 1 (
  echo ERROR: Docker Compose could not start the backend stack.
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
  echo WARNING: The frontend did not become ready. Review .data\frontend.log
)

start "" "http://localhost:8513"
echo Ready. Backend: http://localhost:8514  Frontend: http://localhost:8513
exit /b 0

:install_failed
echo ERROR: winget could not install a required prerequisite.
pause
exit /b 1
