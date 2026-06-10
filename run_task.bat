@echo off
REM ?????????
set PATH=D:\Project\Python;D:\Project\Python\Scripts;%PATH%
set PYTHONPATH=D:\Project\arxiv-daily

REM ???????????
set HTTP_PROXY=http://proxy.hk.hihonor.com:8080
set HTTPS_PROXY=http://proxy.hk.hihonor.com:8080

REM ???????
cd /d D:\Project\arxiv-daily

REM ?????????
echo [%DATE% %TIME%] Starting arxiv-daily task >> task_log.txt
echo PATH=%PATH% >> task_log.txt
echo Working Dir=%CD% >> task_log.txt
echo HTTP_PROXY=%HTTP_PROXY% >> task_log.txt
echo HTTPS_PROXY=%HTTPS_PROXY% >> task_log.txt

REM ?? Python ??
D:\Project\Python\python.exe scripts\run_daily.py --skip_download >> task_log.txt 2>&1

if %ERRORLEVEL% EQU 0 (
    echo [%DATE% %TIME%] Task completed successfully >> task_log.txt
) else (
    echo [%DATE% %TIME%] Task failed with error code %ERRORLEVEL% >> task_log.txt
)
