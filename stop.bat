@echo off
chcp 65001 >nul
echo 停止拾忆服务...
taskkill /FI "WindowTitle eq 拾忆-后端*" /T /F >nul 2>&1
taskkill /FI "WindowTitle eq 拾忆-前端*" /T /F >nul 2>&1
echo 已停止。
