#!/bin/bash
# HFinance 一键部署脚本
# 使用方法: sudo bash deploy/deploy.sh

set -e

INSTALL_DIR="/opt/hfinance"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "==================================="
echo "  HFinance 一键部署"
echo "==================================="

# 1. 创建安装目录
echo "[1/6] 创建安装目录..."
mkdir -p $INSTALL_DIR

# 2. 复制项目文件
echo "[2/6] 复制项目文件..."
rsync -av --exclude='.venv' --exclude='node_modules' --exclude='__pycache__' --exclude='.git' \
    "$PROJECT_DIR/" "$INSTALL_DIR/"

# 3. 后端安装依赖
echo "[3/6] 安装后端依赖..."
cd $INSTALL_DIR/backend
if command -v uv &> /dev/null; then
    uv sync
else
    pip install -r requirements.txt 2>/dev/null || pip install -e .
fi

# 4. 前端构建
echo "[4/6] 构建前端..."
cd $INSTALL_DIR/frontend
if [ -d "node_modules" ]; then
    pnpm install
fi
pnpm build

# 5. 配置 Nginx
echo "[5/6] 配置 Nginx..."
cp $INSTALL_DIR/deploy/nginx/hfinance.conf /etc/nginx/sites-available/hfinance
ln -sf /etc/nginx/sites-available/hfinance /etc/nginx/sites-enabled/hfinance
nginx -t && systemctl reload nginx

# 6. 配置 Systemd
echo "[6/6] 配置 Systemd..."
cp $INSTALL_DIR/deploy/systemd/hfinance.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable hfinance
systemctl restart hfinance

echo ""
echo "==================================="
echo "  部署完成！"
echo "==================================="
echo ""
echo "后端服务: http://localhost:8820"
echo "前端页面: http://localhost (Nginx 代理)"
echo ""
echo "常用命令："
echo "  查看日志: journalctl -u hfinance -f"
echo "  重启服务: systemctl restart hfinance"
echo "  停止服务: systemctl stop hfinance"
echo ""
