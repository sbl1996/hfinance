"""行情缓存 Repository"""

from app.db.connection import get_db


async def get_latest_price(code: str) -> dict | None:
    """获取某标的最新缓存价格"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM price_cache WHERE code = ? ORDER BY price_date DESC LIMIT 1",
        (code,),
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def get_price_by_date(code: str, price_date: str) -> dict | None:
    """获取某标的指定日期的价格"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM price_cache WHERE code = ? AND price_date = ?",
        (code, price_date),
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def upsert_price(code: str, price: float, currency: str, price_date: str, source: str = "akshare", is_stale: bool = False, growth_rate: float = 0.0) -> dict:
    """写入价格缓存（UNIQUE 约束自动替换）"""
    db = await get_db()
    await db.execute(
        """INSERT OR REPLACE INTO price_cache (code, price, currency, price_date, growth_rate, source, is_stale, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))""",
        (code, price, currency, price_date, growth_rate, source, int(is_stale)),
    )
    await db.commit()
    return await get_latest_price(code)


async def get_all_latest_prices() -> list[dict]:
    """获取所有标的的最新缓存价格"""
    db = await get_db()
    cursor = await db.execute(
        """SELECT pc.* FROM price_cache pc
           INNER JOIN (
               SELECT code, MAX(price_date) as max_date FROM price_cache GROUP BY code
           ) latest ON pc.code = latest.code AND pc.price_date = latest.max_date"""
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


# ============ 汇率 ============

async def get_latest_rate(pair: str = "HKDCNY") -> dict | None:
    """获取最新汇率"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM exchange_rates WHERE pair = ? ORDER BY rate_date DESC LIMIT 1",
        (pair,),
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def get_rate_by_date(pair: str, rate_date: str) -> dict | None:
    """获取指定日期的汇率"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM exchange_rates WHERE pair = ? AND rate_date = ?",
        (pair, rate_date),
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def upsert_rate(pair: str, rate: float, rate_date: str, source: str = "akshare") -> dict:
    """写入汇率缓存"""
    db = await get_db()
    await db.execute(
        """INSERT OR REPLACE INTO exchange_rates (pair, rate, rate_date, source, created_at)
           VALUES (?, ?, ?, ?, datetime('now', 'localtime'))""",
        (pair, rate, rate_date, source),
    )
    await db.commit()
    return await get_latest_rate(pair)
