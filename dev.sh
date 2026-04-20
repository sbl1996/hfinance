#!/bin/bash
# HFinance 开发环境启动脚本
# 同时启动后端和前端开发服务器
# 使用方法: bash dev.sh

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🚀 启动 HFinance 开发环境..."

# 启动后端 (FastAPI + Uvicorn)
echo "📡 启动后端服务 (http://localhost:8000)..."
cd "$PROJECT_DIR/backend"
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# 启动前端 (Vite dev server)
echo "🎨 启动前端服务 (http://localhost:5173)..."
cd "$PROJECT_DIR/frontend"
pnpm dev &
FRONTEND_PID=$!

echo ""
echo "✅ 开发环境已启动："
echo "   后端 API:  http://localhost:8000"
echo "   前端页面:  http://localhost:5173"
echo "   API 代理:  /api -> http://localhost:8000"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 捕获退出信号，清理子进程
cleanup() {
    echo ""
    echo "🛑 停止服务..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    wait $BACKEND_PID 2>/dev/null
    wait $FRONTEND_PID 2>/dev/null
    echo "✅ 已停止"
}
trap cleanup EXIT INT TERM

# 等待子进程
wait
