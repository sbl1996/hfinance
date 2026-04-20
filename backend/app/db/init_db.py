"""数据库初始化：建表、确保必要记录存在"""

from pathlib import Path

from app.db.connection import get_db

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


async def init_database():
    """初始化数据库：读取 schema.sql 并执行建表"""
    db = await get_db()
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    await db.executescript(schema_sql)
    await db.commit()
