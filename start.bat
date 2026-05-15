@echo off
chcp 65001 >nul
echo ============================
echo   拾忆 - AI叙事游戏 启动器
echo ============================
echo.

REM 创建 PID 目录
if not exist ".pids" mkdir ".pids"

REM 获取脚本所在目录
set "ROOT=%~dp0"

REM 检查 .env
if not exist "%ROOT%.env" (
    echo [错误] 未找到 .env 文件
    echo 请复制 .env.example 为 .env 并填入 API Key
    pause
    exit /b 1
)

REM 检查 node_modules
if not exist "%ROOT%frontend\node_modules" (
    echo 正在安装前端依赖...
    cd "%ROOT%frontend"
    call npm install
    cd "%ROOT%"
)

REM 启动后端
echo 启动后端...
cd "%ROOT%"
start "拾忆-后端" cmd /c "python -m backend.main"
echo 后端启动中...

REM 等待后端就绪
timeout /t 3 /nobreak >nul

REM 启动前端
echo 启动前端...
cd "%ROOT%frontend"
start "拾忆-前端" cmd /c "npm run dev"

echo.
echo ============================
echo   拾忆启动完成！
echo   前端: http://localhost:5173
echo   后端: http://localhost:8000
echo   按任意键关闭此窗口（服务继续运行）
echo ============================
pause >nul
