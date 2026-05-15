@echo off
chcp 65001 >nul
echo.
echo  ╔══════════════════════════════════════╗
echo  ║    拾忆 · Memory Healer - 启动      ║
echo  ╚══════════════════════════════════════╝
echo.

:: 检查 .env
if not exist ".env" (
    echo [错误] 未找到 .env 文件
    echo 请复制 .env.example 为 .env 并填入 DEEPSEEK_API_KEY
    pause
    exit /b 1
)

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.11+
    pause
    exit /b 1
)

:: 检查 Node
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Node.js，请先安装 Node.js 18+
    pause
    exit /b 1
)

echo [1/4] 安装后端依赖...
pip install -r requirements.txt -q

echo [2/4] 安装前端依赖...
cd frontend
call npm install --silent
cd ..

echo [3/4] 启动后端 (端口 8000)...
start "拾忆-后端" cmd /c "cd backend && python main.py"

:: 等后端启动
timeout /t 3 /nobreak >nul

echo [4/4] 启动前端 (端口 5173)...
start "拾忆-前端" cmd /c "cd frontend && npm run dev"

echo.
echo  ╔══════════════════════════════════════╗
echo  ║  启动完成！                          ║
echo  ║  前端: http://localhost:5173         ║
echo  ║  后端: http://localhost:8000         ║
echo  ║  API文档: http://localhost:8000/docs ║
echo  ╚══════════════════════════════════════╝
echo.
echo 按任意键关闭此窗口...
pause >nul
