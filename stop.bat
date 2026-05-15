@echo off
chcp 65001 >nul
echo 正在停止拾忆...

REM 停止后端
if exist ".pids\backend.pid" (
    set /p BACKEND_PID=<".pids\backend.pid"
    taskkill /PID %BACKEND_PID% /F >nul 2>&1
    del ".pids\backend.pid" >nul 2>&1
    echo 后端已停止
) else (
    echo 后端未运行（无 PID 文件）
)

REM 停止前端
if exist ".pids\frontend.pid" (
    set /p FRONTEND_PID=<".pids\frontend.pid"
    taskkill /PID %FRONTEND_PID% /F >nul 2>&1
    del ".pids\frontend.pid" >nul 2>&1
    echo 前端已停止
) else (
    echo 前端未运行（无 PID 文件）
)

REM 清理 PID 目录
if exist ".pids" rmdir ".pids" >nul 2>&1

echo 拾忆已停止
