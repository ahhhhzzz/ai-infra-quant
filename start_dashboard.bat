@echo off
setlocal EnableExtensions

set "REPO_ROOT=%~dp0"
set "PYTHON_EXE=%REPO_ROOT%.venv\Scripts\python.exe"
set "DASHBOARD_URL=http://127.0.0.1:8000"
set "HEALTH_URL=%DASHBOARD_URL%/health"
set "OPEND_TIMEOUT_SECONDS=60"
set "FASTAPI_TIMEOUT_SECONDS=45"

pushd "%REPO_ROOT%" >nul

echo [1/4] Checking Futu OpenD...
call :tcp_ready 127.0.0.1 11111
if not errorlevel 1 goto opend_ready

call :resolve_opend
if errorlevel 1 goto opend_not_found

echo [2/4] Starting Futu OpenD and waiting for port 11111...
start "Futu OpenD" "%OPEND_EXE%"
call :wait_for_tcp 127.0.0.1 11111 %OPEND_TIMEOUT_SECONDS%
if errorlevel 1 goto opend_timeout
goto opend_ready

:opend_ready
echo [2/4] Futu OpenD is reachable on 127.0.0.1:11111.

if not exist "%PYTHON_EXE%" goto python_missing

echo [3/4] Checking AI Infra Quant...
call :health_ready
if not errorlevel 1 goto dashboard_ready

call :tcp_ready 127.0.0.1 8000
if not errorlevel 1 goto port_conflict

echo [3/4] Starting AI Infra Quant in a separate console...
set "MARKET_DATA_PROVIDER=futu"
start "AI Infra Quant Dashboard" "%ComSpec%" /k ""%PYTHON_EXE%" -m uvicorn ai_infra_quant.backend.main:app --host 127.0.0.1 --port 8000"

call :wait_health %FASTAPI_TIMEOUT_SECONDS%
if errorlevel 1 goto fastapi_timeout

:dashboard_ready
echo [4/4] Opening Dashboard...
start "" "%DASHBOARD_URL%"
popd
exit /b 0

:resolve_opend
set "OPEND_EXE="
if defined FUTU_OPEND_EXE (
  if exist "%FUTU_OPEND_EXE%" (
    set "OPEND_EXE=%FUTU_OPEND_EXE%"
    exit /b 0
  )
  echo [INFO] FUTU_OPEND_EXE is set but does not point to an existing file.
)
if exist "%APPDATA%\Futu_OpenD\Futu_OpenD.exe" set "OPEND_EXE=%APPDATA%\Futu_OpenD\Futu_OpenD.exe"
if not defined OPEND_EXE if exist "%LOCALAPPDATA%\Futu_OpenD\Futu_OpenD.exe" set "OPEND_EXE=%LOCALAPPDATA%\Futu_OpenD\Futu_OpenD.exe"
if not defined OPEND_EXE if exist "%ProgramFiles%\Futu_OpenD\Futu_OpenD.exe" set "OPEND_EXE=%ProgramFiles%\Futu_OpenD\Futu_OpenD.exe"
if not defined OPEND_EXE if defined ProgramFiles(x86) if exist "%ProgramFiles(x86)%\Futu_OpenD\Futu_OpenD.exe" set "OPEND_EXE=%ProgramFiles(x86)%\Futu_OpenD\Futu_OpenD.exe"
if defined OPEND_EXE exit /b 0
exit /b 1

:tcp_ready
powershell.exe -NoProfile -NonInteractive -Command "$client = New-Object System.Net.Sockets.TcpClient; try { $result = $client.BeginConnect('%~1', %~2, $null, $null); if (-not $result.AsyncWaitHandle.WaitOne(1000, $false)) { exit 1 }; $client.EndConnect($result); exit 0 } catch { exit 1 } finally { $client.Dispose() }" >nul 2>&1
exit /b %errorlevel%

:wait_for_tcp
powershell.exe -NoProfile -NonInteractive -Command "$deadline = [DateTime]::UtcNow.AddSeconds(%~3); do { $client = New-Object System.Net.Sockets.TcpClient; try { $result = $client.BeginConnect('%~1', %~2, $null, $null); if ($result.AsyncWaitHandle.WaitOne(1000, $false)) { $client.EndConnect($result); exit 0 } } catch {} finally { $client.Dispose() }; Start-Sleep -Seconds 1 } while ([DateTime]::UtcNow -lt $deadline); exit 1" >nul 2>&1
exit /b %errorlevel%

:health_ready
powershell.exe -NoProfile -NonInteractive -Command "try { $health = Invoke-RestMethod -Uri '%HEALTH_URL%' -TimeoutSec 2; if ($health.status -eq 'OK' -and $health.database -eq 'READY') { exit 0 } } catch {}; exit 1" >nul 2>&1
exit /b %errorlevel%

:wait_health
powershell.exe -NoProfile -NonInteractive -Command "$deadline = [DateTime]::UtcNow.AddSeconds(%~1); do { try { $health = Invoke-RestMethod -Uri '%HEALTH_URL%' -TimeoutSec 2; if ($health.status -eq 'OK' -and $health.database -eq 'READY') { exit 0 } } catch {}; Start-Sleep -Seconds 1 } while ([DateTime]::UtcNow -lt $deadline); exit 1" >nul 2>&1
exit /b %errorlevel%

:opend_not_found
echo [ERROR] Futu OpenD is not reachable and Futu_OpenD.exe could not be found.
echo Set FUTU_OPEND_EXE once, then launch this file again. Example:
echo   setx FUTU_OPEND_EXE "C:\path\to\Futu_OpenD.exe"
goto fail

:opend_timeout
echo [ERROR] Futu OpenD did not become reachable on 127.0.0.1:11111 within %OPEND_TIMEOUT_SECONDS% seconds.
echo Complete any required OpenD login or setup, then try again.
goto fail

:python_missing
echo [ERROR] Repository Python was not found at .venv\Scripts\python.exe.
echo Complete the README local setup first; this launcher does not install dependencies.
goto fail

:port_conflict
echo [ERROR] Port 8000 is occupied, but the AI Infra Quant health endpoint is not healthy.
echo Stop the conflicting application and try again. No process was terminated.
goto fail

:fastapi_timeout
echo [ERROR] AI Infra Quant did not become healthy at %HEALTH_URL% within %FASTAPI_TIMEOUT_SECONDS% seconds.
echo Review the separate FastAPI console for the startup error.
goto fail

:fail
popd
pause
exit /b 1
