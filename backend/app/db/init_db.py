"""数据库初始化：建表、确保必要记录存在"""

from pathlib import Path

from app.db.connection import get_db

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


async def init_database():
    """初始化数据库：读取 schema.sql 并执行建表"""
    db = await get_db()
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    await db.executescript(schema_sql)
    cursor = await db.execute("PRAGMA table_info(holding_sort_orders)")
    columns = {row[1] for row in await cursor.fetchall()}
    if "ignored" not in columns:
        await db.execute(
            "ALTER TABLE holding_sort_orders ADD COLUMN ignored INTEGER NOT NULL DEFAULT 0"
        )
    await db.execute(
        """
        INSERT INTO holding_sort_orders (holding_id, sort_order, ignored)
        SELECT h.id, h.id, 0
        FROM holdings h
        LEFT JOIN holding_sort_orders hso ON hso.holding_id = h.id
        WHERE hso.holding_id IS NULL
        """
    )
    cursor = await db.execute("PRAGMA table_info(fetch_tasks)")
    fetch_task_columns = {row[1] for row in await cursor.fetchall()}
    if "code" not in fetch_task_columns:
        await db.execute("ALTER TABLE fetch_tasks ADD COLUMN code TEXT")
    if "name" not in fetch_task_columns:
        await db.execute("ALTER TABLE fetch_tasks ADD COLUMN name TEXT")
    if "market" not in fetch_task_columns:
        await db.execute("ALTER TABLE fetch_tasks ADD COLUMN market TEXT")
    await db.execute(
        """
        UPDATE fetch_tasks
        SET
            code = COALESCE(code, ''),
            name = COALESCE(name, ''),
            market = COALESCE(market, 'A_STOCK')
        """
    )
    await db.commit()
