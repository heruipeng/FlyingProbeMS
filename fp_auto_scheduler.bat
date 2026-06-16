@echo off
setlocal enabledelayedexpansion

set "PY_SCRIPT=fp_auto_scheduler.py"

:: 精确检测 Python 脚本是否正在运行（100% 准确）
wmic process where "name='python.exe' or name='pythonw.exe'" get commandline | findstr /i "%PY_SCRIPT%" >nul
if %errorlevel% equ 0 (
    echo [%date% %time%] 脚本已在运行，不重复启动
    exit
)

:: 脚本未运行 → 启动
set "SCRIPT_DIR=D:\eastek-server\ezFixtureII\sys\scripts\FlyingProbeMS"
cd /d "%SCRIPT_DIR%"
echo [%date% %time%] 启动 %PY_SCRIPT%
start "%PY_SCRIPT%" python "%PY_SCRIPT%" JM1 JM2
exit
REM PAUSE