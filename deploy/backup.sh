#!/bin/bash
# HFinance 数据库备份脚本
# 使用方法: bash deploy/backup.sh
# 建议添加 crontab: 0 2 * * * bash /opt/hfinance/deploy/backup.sh

set -e

DB_PATH="${HFINANCE_DB_PATH:-/opt/hfinance/backend/data/hfinance.db}"
BACKUP_DIR="/opt/hfinance/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
KEEP_DAYS=30

mkdir -p $BACKUP_DIR

# SQLite 安全备份（使用 .backup 命令确保一致性）
echo "备份数据库: $DB_PATH"
sqlite3 "$DB_PATH" ".backup '$BACKUP_DIR/hfinance_$TIMESTAMP.db'"

# 压缩备份
gzip "$BACKUP_DIR/hfinance_$TIMESTAMP.db"
echo "备份完成: $BACKUP_DIR/hfinance_$TIMESTAMP.db.gz"

# 清理过期备份
find $BACKUP_DIR -name "hfinance_*.db.gz" -mtime +$KEEP_DAYS -delete
echo "已清理 ${KEEP_DAYS} 天前的旧备份"
