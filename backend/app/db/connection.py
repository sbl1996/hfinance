"""SQLite 异步连接管理"""

import logging

import aiosqlite

from app.core.config import get_settings

_db: aiosqlite.Connection | None = None
logger = logging.getLogger(__name__)


async def get_db() -> aiosqlite.Connection:
    """获取数据库连接（单例模式）"""
    global _db
    if _db is None:
        settings = get_settings()
        _db = await aiosqlite.connect(settings.DB_PATH)
        _db.row_factory = aiosqlite.Row
        # 开启外键约束
        await _db.execute("PRAGMA foreign_keys = ON")
        await _db.execute("PRAGMA busy_timeout = 5000")
        await _db.execute(f"PRAGMA journal_mode = {settings.DB_JOURNAL_MODE}")
        logger.info("SQLite 已连接: path=%s journal_mode=%s", settings.DB_PATH, settings.DB_JOURNAL_MODE)
    return _db


async def close_db():
    """关闭数据库连接"""
    global _db
    if _db is not None:
        await _db.close()
        _db = None
