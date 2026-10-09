: << 'CMDBLOCK'
@echo off
REM A cross-platform polyglot wrapper for hook scripts.
REM On Windows: cmd.exe runs this batch part, and the batch part finds and calls bash.
REM On Unix: the shell treats this as a normal bash script (":" is a no-op).
REM
REM The hook script uses a file name WITHOUT an extension (for example
REM "check-protected-paths", not "check-protected-paths.sh"), because Claude
REM Code on Windows has an auto-detect feature that adds "bash" before a
REM command with ".sh" — that feature is not reliable (it does not scan
REM common Git Bash install locations, and it has no clean fallback when
REM bash is missing), so this wrapper does that job itself instead.
REM
REM Usage: run-hook.cmd <script-name> [args...]

if "%~1"=="" (
    echo run-hook.cmd: missing script name >&2
    exit /b 1
)

set "HOOK_DIR=%~dp0"

REM Try Git for Windows bash at the standard install locations
if exist "C:\Program Files\Git\bin\bash.exe" (
    "C:\Program Files\Git\bin\bash.exe" "%HOOK_DIR%%~1" %2 %3 %4 %5 %6 %7 %8 %9
    exit /b %ERRORLEVEL%
)
if exist "C:\Program Files (x86)\Git\bin\bash.exe" (
    "C:\Program Files (x86)\Git\bin\bash.exe" "%HOOK_DIR%%~1" %2 %3 %4 %5 %6 %7 %8 %9
    exit /b %ERRORLEVEL%
)

REM Try bash available on PATH (self-installed Git Bash, MSYS2, Cygwin...)
where bash >nul 2>nul
if %ERRORLEVEL% equ 0 (
    bash "%HOOK_DIR%%~1" %2 %3 %4 %5 %6 %7 %8 %9
    exit /b %ERRORLEVEL%
)

REM Could not find bash - exit quietly instead of showing an error
REM (the plugin still works, this machine just misses this hook)
exit /b 0
CMDBLOCK

# Unix: run the named script directly
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_NAME="$1"
shift
exec bash "${SCRIPT_DIR}/${SCRIPT_NAME}" "$@"
