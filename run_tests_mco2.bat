@echo off
REM ===================================================================
REM run_tests_mco2.bat - Windows version of the MCO2 traceroute runner.
REM
REM Runs the three required traces with labeled banners, pauses after
REM each so you can screenshot it, and saves a transcript to
REM traceroute_output.log.
REM
REM USAGE:  Right-click Command Prompt -> "Run as administrator", then:
REM         run_tests_mco2.bat
REM
REM Put this file in the SAME folder as traceroute.py.
REM ===================================================================
setlocal enabledelayedexpansion

set "PYTHON=python"
set "SCRIPT_DIR=%~dp0"
set "TR=%SCRIPT_DIR%traceroute.py"
set "LOGFILE=%SCRIPT_DIR%traceroute_output.log"
set "TMPFILE=%SCRIPT_DIR%_trace_tmp.txt"

set "HOST1=google.com"
set "HOST2=dlsu.instructure.com"
set "HOST3=dlsu.edu.ph"

REM ---- Require administrator (raw sockets need it) -------------------
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: raw sockets need administrator privileges.
    echo Right-click Command Prompt and choose "Run as administrator",
    echo then run this script again.
    exit /b 1
)

if not exist "%TR%" (
    echo ERROR: could not find traceroute.py at: %TR%
    echo Place this .bat in the same folder as traceroute.py.
    exit /b 1
)

REM ---- Fresh log -----------------------------------------------------
type nul > "%LOGFILE%"

echo MCO2 Traceroute - Test Runner (Windows)
echo Log file: %LOGFILE%
echo NOTE: a full 30-hop trace with timeouts can take a few minutes.
echo       If every hop times out, allow ICMP in Windows Defender
echo       Firewall or temporarily disable it (see assignment reminders).
echo.
pause

call :run_trace "TRACE 1: %HOST1%" "%HOST1%"
call :run_trace "TRACE 2: %HOST2%" "%HOST2%"
call :run_trace "TRACE 3: %HOST3%" "%HOST3%"

call :banner "ALL TRACES COMPLETE"
echo A full text transcript was saved to: %LOGFILE%
echo Now collect your screenshots for the documentation.
del "%TMPFILE%" >nul 2>&1
exit /b 0

REM ===================================================================
:banner
echo.>> "%LOGFILE%"
echo ===================================================================>> "%LOGFILE%"
echo   %~1>> "%LOGFILE%"
echo ===================================================================>> "%LOGFILE%"
echo.
echo ===================================================================
echo   %~1
echo ===================================================================
exit /b 0

:run_trace
call :banner %1
echo $ %PYTHON% traceroute.py %~2
echo $ %PYTHON% traceroute.py %~2>> "%LOGFILE%"
echo.
echo.>> "%LOGFILE%"
"%PYTHON%" "%TR%" %~2 > "%TMPFILE%" 2>&1
type "%TMPFILE%"
type "%TMPFILE%" >> "%LOGFILE%"
echo.
echo ^>^>^> Take your screenshot, then press any key for the next trace...
pause >nul
exit /b 0
