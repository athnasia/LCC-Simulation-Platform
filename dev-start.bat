@echo off
chcp 65001 >nul
title LCC App 一键启动

echo ============================================
echo   LCC App - 工业互联网成本建模平台
echo   一键启动脚本
echo ============================================
echo.

:: 释放端口 8001 (后端)
echo [1/4] 检查并释放端口 8001...
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":8001 "') do (
    taskkill /F /PID %%a >nul 2>nul
)

:: 释放端口 5173 (前端)
echo [2/4] 检查并释放端口 5173...
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":5173 "') do (
    taskkill /F /PID %%a >nul 2>nul
)

:: 启动后端
echo [3/4] 启动 FastAPI 后端 (端口 8001)...
start "LCC-Backend" cmd /k "cd /d %~dp0backend && .venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8001 --reload && pause"

:: 等待后端启动
timeout /t 3 /nobreak >nul

:: 启动前端
echo [4/4] 启动 Vue3 前端开发服务器 (端口 5173)...
start "LCC-Frontend" cmd /k "cd /d %~dp0frontend && pnpm dev && pause"

echo.
echo ============================================
echo   启动完成！约 5 秒后可访问：
echo.
echo   前端页面：http://localhost:5173
echo   API 文档：http://127.0.0.1:8001/docs
echo   默认账号：admin / 123456
echo ============================================
echo.
pause
