"""数据库初始化：建表、确保必要记录存在"""

from pathlib import Path

from app.db.connection import get_db

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


async def init_database():
    """初始化数据库：读取 schema.sql 并执行建表，再执行增量迁移"""
    db = await get_db()
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    await db.executescript(schema_sql)
    await db.commit()

    # 增量迁移：为已有表添加新列
    await _migrate_add_growth_rate(db)


async def _migrate_add_growth_rate(db):
    """为 price_cache 表添加 growth_rate 列（如尚不存在）"""
    cursor = await db.execute("PRAGMA table_info(price_cache)")
    columns = [row[1] for row in await cursor.fetchall()]
    if "growth_rate" not in columns:
        await db.execute("ALTER TABLE price_cache ADD COLUMN growth_rate REAL NOT NULL DEFAULT 0")
        await db.commit()
