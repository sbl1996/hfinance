"""SQLite 异步连接管理"""

import aiosqlite

from app.core.config import get_settings

_db: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    """获取数据库连接（单例模式）"""
    global _db
    if _db is None:
        settings = get_settings()
        _db = await aiosqlite.connect(settings.DB_PATH)
        _db.row_factory = aiosqlite.Row
        # 开启外键约束
        await _db.execute("PRAGMA foreign_keys = ON")
        # WAL 模式，提升并发读写性能
        await _db.execute("PRAGMA journal_mode = WAL")
    return _db


async def close_db():
    """关闭数据库连接"""
    global _db
    if _db is not None:
        await _db.close()
        _db = None
