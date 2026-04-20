#!/bin/bash
# HFinance 一键部署脚本
# 使用方法: bash deploy/deploy.sh
# 需要 sudo 权限的步骤会自动提权，其余在用户环境下执行

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DEPLOY_USER="$(whoami)"

echo "==================================="
echo "  HFinance 一键部署"
echo "==================================="

# 1. 后端安装依赖（用户环境）
echo "[1/3] 安装后端依赖..."
cd "$PROJECT_DIR/backend"
source .venv/bin/activate
UV_INDEX_URL=https://mirrors.aliyun.com/pypi/simple uv sync

# 2. 前端构建（用户环境）
echo "[2/3] 构建前端..."
cd "$PROJECT_DIR/frontend"
pnpm install
pnpm build

# 3. 配置系统服务（需要 sudo）
echo "[3/3] 配置系统服务..."

# Nginx：将前端构建产物复制到 /var/www/hfinance
sudo rm -rf /var/www/hfinance
sudo cp -r "$PROJECT_DIR/frontend/dist" /var/www/hfinance
sudo chown -R www-data:www-data /var/www/hfinance
sudo cp "$PROJECT_DIR/deploy/nginx/hfinance.conf" /etc/nginx/sites-available/hfinance
sudo ln -sf /etc/nginx/sites-available/hfinance /etc/nginx/sites-enabled/hfinance
sudo nginx -t && sudo systemctl reload nginx

# Systemd：替换用户名和工作目录为实际路径
sudo sed -e "s/__DEPLOY_USER__/$DEPLOY_USER/g" \
    -e "s|__PROJECT_DIR__|$PROJECT_DIR|g" \
    "$PROJECT_DIR/deploy/systemd/hfinance.service" \
    > /tmp/hfinance.service
sudo cp /tmp/hfinance.service /etc/systemd/system/
rm -f /tmp/hfinance.service
sudo systemctl daemon-reload
sudo systemctl enable hfinance
sudo systemctl restart hfinance

echo ""
echo "==================================="
echo "  部署完成！"
echo "==================================="
echo ""
echo "后端服务: http://localhost:8820"
echo "前端页面: http://localhost:8821 (Nginx 代理)"
echo ""
echo "常用命令："
echo "  查看日志: journalctl -u hfinance -f"
echo "  重启服务: sudo systemctl restart hfinance"
echo "  停止服务: sudo systemctl stop hfinance"
echo ""
