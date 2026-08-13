@echo off
setlocal EnableExtensions

title Claude Code via Remote OmniRoute (Laptop)

REM ============================================================
REM USER CONFIG
REM ============================================================

REM 1) Base URL из OmniRoute. Теперь указывает на твой ноут!
set "OMNI_BASE_URL=http://192.168.0.3:20128"

REM 2) API Key из OmniRoute.
set "OMNI_API_KEY=sk-6a55df036373ab4d-8fdb2b-604dadeb"

REM 3) Модель или combo из OmniRoute (Sonnet 4.5 для Kiro AI).
set "CLAUDE_MAIN_MODEL=kr/claude-sonnet-4.5"

REM 4) Быстрая модель для фоновых задач.
set "CLAUDE_FAST_MODEL=kr/claude-haiku-4.5"

REM 5) Команда запуска OmniRoute (здесь не используется, так как сервер на ноуте).
set "OMNI_COMMAND=omniroute"

REM 6) Сколько секунд ждать подключения к ноуту.
set "WAIT_TIMEOUT=90"

REM ============================================================
REM INTERNAL CONFIG
REM ============================================================

REM Достаем порт из OMNI_BASE_URL автоматически.
for /f "usebackq delims=" %%P in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "$u='%OMNI_BASE_URL%'; try { ([Uri]$u).Port } catch { -1 }"`) do set "OMNI_PORT=%%P"

for /f "usebackq delims=" %%H in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "$u='%OMNI_BASE_URL%'; try { ([Uri]$u).Host } catch { 'localhost' }"`) do set "OMNI_HOST=%%H"

if "%OMNI_PORT%"=="-1" (
    echo [ERROR] Cannot read port from OMNI_BASE_URL.
    echo Check this line in the bat file:
    echo OMNI_BASE_URL=%OMNI_BASE_URL%
    echo.
    pause
    exit /b 1
)

if "%OMNI_PORT%"=="" (
    echo [ERROR] Cannot read port from OMNI_BASE_URL.
    echo Check this line in the bat file:
    echo OMNI_BASE_URL=%OMNI_BASE_URL%
    echo.
    pause
    exit /b 1
)

if /I "%OMNI_HOST%"=="localhost" set "OMNI_CHECK_HOST=127.0.0.1"
if not defined OMNI_CHECK_HOST set "OMNI_CHECK_HOST=%OMNI_HOST%"

REM ============================================================
REM BASIC CHECKS
REM ============================================================

where claude >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Claude Code is not installed or not found in PATH.
    echo.
    echo Install it with:
    echo winget install Anthropic.ClaudeCode
    echo.
    pause
    exit /b 1
)

REM ============================================================
REM CHECK REMOTE OMNIROUTE CONNECTION
REM ============================================================

echo [INFO] Connecting to OmniRoute on your laptop...
echo [INFO] Host: %OMNI_CHECK_HOST%
echo [INFO] Port: %OMNI_PORT%

set /a ELAPSED=0

:WAIT_LOOP
call :PortOpen "%OMNI_CHECK_HOST%" "%OMNI_PORT%"

if not errorlevel 1 goto OMNI_READY

if %ELAPSED% GEQ %WAIT_TIMEOUT% (
    echo [ERROR] Cannot connect to OmniRoute on %OMNI_CHECK_HOST%
    echo.
    echo 1. Убедись, что на ноуте запущена команда "omniroute".
    echo 2. Убедись, что комп и ноут подключены к одному Wi-Fi.
    echo 3. Возможно, брандмауэр Windows на ноуте блокирует порт 20128.
    echo.
    pause
    exit /b 1
)

timeout /t 2 /nobreak >nul
set /a ELAPSED+=2
goto WAIT_LOOP

:OMNI_READY
echo [OK] Successfully connected to laptop: %OMNI_BASE_URL%

REM ============================================================
REM SET CLAUDE CODE VARIABLES
REM ============================================================

set "ANTHROPIC_BASE_URL=%OMNI_BASE_URL%"
set "ANTHROPIC_AUTH_TOKEN=%OMNI_API_KEY%"
set "ANTHROPIC_MODEL=%CLAUDE_MAIN_MODEL%"

set "ANTHROPIC_DEFAULT_SONNET_MODEL=%CLAUDE_MAIN_MODEL%"
set "ANTHROPIC_DEFAULT_OPUS_MODEL=%CLAUDE_MAIN_MODEL%"
set "ANTHROPIC_DEFAULT_HAIKU_MODEL=%CLAUDE_FAST_MODEL%"
set "ANTHROPIC_SMALL_FAST_MODEL=%CLAUDE_FAST_MODEL%"

set "ANTHROPIC_API_KEY="
set "CLAUDE_CODE_OAUTH_TOKEN="

REM Чтобы трафик к ноуту не уходил через прокси/VPN
set "NO_PROXY=%OMNI_CHECK_HOST%,localhost,127.0.0.1"
set "no_proxy=%OMNI_CHECK_HOST%,localhost,127.0.0.1"

echo.
echo [INFO] Starting Claude Code...
echo [INFO] Main model: %ANTHROPIC_MODEL%
echo.

claude %*

exit /b %ERRORLEVEL%

REM ============================================================
REM FUNCTION: CHECK IF PORT IS OPEN
REM ============================================================

:PortOpen
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$client = New-Object Net.Sockets.TcpClient; try { $iar = $client.BeginConnect('%~1', [int]%~2, $null, $null); if (-not $iar.AsyncWaitHandle.WaitOne(1500, $false)) { $client.Close(); exit 1 }; $client.EndConnect($iar); $client.Close(); exit 0 } catch { exit 1 }" >nul 2>nul

exit /b %ERRORLEVEL%