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
    await _migrate_holdings_currency_column(db)
    await _migrate_price_cache_currency_check(db)
    await _migrate_watchlist_items_market_check(db)
    await _migrate_watchlist_items_currency_column(db)
    await _migrate_fetch_task_market_check(db)
    await db.commit()


async def _migrate_holdings_currency_column(db):
    """为 holdings 增加 currency 列。"""
    cursor = await db.execute("PRAGMA table_info(holdings)")
    columns = {row[1] for row in await cursor.fetchall()}
    if "currency" in columns:
        return
    await db.execute(
        "ALTER TABLE holdings ADD COLUMN currency TEXT NOT NULL DEFAULT 'CNY'"
    )


async def _migrate_price_cache_currency_check(db):
    """重建 price_cache 以允许写入 USD 币种。"""
    cursor = await db.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'price_cache'"
    )
    row = await cursor.fetchone()
    create_sql = (row[0] if row else "") or ""
    if "'USD'" in create_sql:
        return

    await db.executescript(
        """
        ALTER TABLE price_cache RENAME TO price_cache_old;
        CREATE TABLE price_cache (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            code         TEXT    NOT NULL,
            price        REAL    NOT NULL,
            currency     TEXT    NOT NULL DEFAULT 'CNY' CHECK(currency IN ('CNY', 'HKD', 'USD')),
            price_date   TEXT    NOT NULL,
            source       TEXT    NOT NULL DEFAULT 'akshare',
            created_at   TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
            UNIQUE(code, price_date)
        );
        INSERT INTO price_cache (id, code, price, currency, price_date, source, created_at)
        SELECT id, code, price, currency, price_date, source, created_at
        FROM price_cache_old;
        DROP TABLE price_cache_old;
        CREATE INDEX IF NOT EXISTS idx_price_cache_code ON price_cache(code);
        CREATE INDEX IF NOT EXISTS idx_price_cache_date ON price_cache(price_date);
        """
    )


async def _migrate_watchlist_items_market_check(db):
    """重建 watchlist_items 以允许自选指数类型。"""
    cursor = await db.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'watchlist_items'"
    )
    row = await cursor.fetchone()
    create_sql = (row[0] if row else "") or ""
    if "'CN_INDEX'" in create_sql:
        return

    await db.executescript(
        """
        ALTER TABLE watchlist_items RENAME TO watchlist_items_old;
        CREATE TABLE watchlist_items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            code        TEXT    NOT NULL,
            name        TEXT    NOT NULL,
            market      TEXT    NOT NULL CHECK(market IN ('A_STOCK', 'HK_STOCK', 'FUND', 'US_STOCK', 'CN_INDEX')),
            currency    TEXT    NOT NULL DEFAULT 'CNY' CHECK(currency IN ('CNY', 'HKD', 'USD')),
            sort_order  INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
            updated_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
        );
        INSERT INTO watchlist_items (id, code, name, market, currency, sort_order, created_at, updated_at)
        SELECT id, code, name, market, 'CNY', sort_order, created_at, updated_at
        FROM watchlist_items_old;
        DROP TABLE watchlist_items_old;
        CREATE INDEX IF NOT EXISTS idx_watchlist_items_sort_order ON watchlist_items(sort_order, id);
        """
    )


async def _migrate_watchlist_items_currency_column(db):
    """为 watchlist_items 增加 currency 列。"""
    cursor = await db.execute("PRAGMA table_info(watchlist_items)")
    columns = {row[1] for row in await cursor.fetchall()}
    if "currency" in columns:
        return
    await db.execute(
        "ALTER TABLE watchlist_items ADD COLUMN currency TEXT NOT NULL DEFAULT 'CNY'"
    )


async def _migrate_fetch_task_market_check(db):
    """重建 fetch_tasks / fetch_task_runs 以允许自选任务市场类型。"""
    cursor = await db.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'fetch_tasks'"
    )
    row = await cursor.fetchone()
    create_sql = (row[0] if row else "") or ""
    if "'CN_INDEX'" in create_sql and "'US_STOCK'" in create_sql:
        return

    await db.execute("PRAGMA foreign_keys = OFF")
    try:
        await db.executescript(
            """
            ALTER TABLE fetch_task_runs RENAME TO fetch_task_runs_old;
            ALTER TABLE fetch_tasks RENAME TO fetch_tasks_old;

            CREATE TABLE fetch_tasks (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                code            TEXT    NOT NULL,
                name            TEXT    NOT NULL,
                market          TEXT    NOT NULL CHECK(market IN ('A_STOCK', 'HK_STOCK', 'FUND', 'US_STOCK', 'CN_INDEX')),
                enabled         INTEGER NOT NULL DEFAULT 1,
                run_time        TEXT    NOT NULL,
                weekdays_mask   INTEGER NOT NULL,
                created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
                updated_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
                UNIQUE(code, market, run_time, weekdays_mask)
            );

            CREATE TABLE fetch_task_runs (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id         INTEGER NOT NULL,
                code            TEXT    NOT NULL,
                name            TEXT    NOT NULL,
                market          TEXT    NOT NULL CHECK(market IN ('A_STOCK', 'HK_STOCK', 'FUND', 'US_STOCK', 'CN_INDEX')),
                scheduled_for   TEXT    NOT NULL,
                status          TEXT    NOT NULL CHECK(status IN ('PENDING', 'RUNNING', 'SUCCESS', 'FAILED')),
                started_at      TEXT,
                finished_at     TEXT,
                error_message   TEXT,
                price_date      TEXT,
                price_value     REAL,
                created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
                updated_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (task_id) REFERENCES fetch_tasks(id) ON DELETE CASCADE,
                UNIQUE(task_id, scheduled_for)
            );

            INSERT INTO fetch_tasks (id, code, name, market, enabled, run_time, weekdays_mask, created_at, updated_at)
            SELECT id, code, name, market, enabled, run_time, weekdays_mask, created_at, updated_at
            FROM fetch_tasks_old;

            INSERT INTO fetch_task_runs (
                id, task_id, code, name, market, scheduled_for, status,
                started_at, finished_at, error_message, price_date, price_value, created_at, updated_at
            )
            SELECT
                id, task_id, code, name, market, scheduled_for, status,
                started_at, finished_at, error_message, price_date, price_value, created_at, updated_at
            FROM fetch_task_runs_old;

            DROP TABLE fetch_task_runs_old;
            DROP TABLE fetch_tasks_old;

            CREATE INDEX IF NOT EXISTS idx_fetch_tasks_enabled_time ON fetch_tasks(enabled, run_time);
            CREATE INDEX IF NOT EXISTS idx_fetch_task_runs_status_scheduled ON fetch_task_runs(status, scheduled_for, id);
            CREATE INDEX IF NOT EXISTS idx_fetch_task_runs_task_scheduled ON fetch_task_runs(task_id, scheduled_for DESC, id DESC);
            CREATE UNIQUE INDEX IF NOT EXISTS idx_fetch_task_runs_one_active
            ON fetch_task_runs(task_id)
            WHERE status IN ('PENDING', 'RUNNING');
            """
        )
    finally:
        await db.execute("PRAGMA foreign_keys = ON")
