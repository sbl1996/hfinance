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


async def get_previous_price(code: str, before_date: str) -> dict | None:
    """获取某标的在指定日期之前最近一次的价格"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM price_cache WHERE code = ? AND price_date < ? ORDER BY price_date DESC LIMIT 1",
        (code, before_date),
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def upsert_price(code: str, price: float, currency: str, price_date: str, source: str = "akshare") -> dict:
    """写入价格缓存（UNIQUE 约束自动替换）"""
    db = await get_db()
    await db.execute(
        """INSERT OR REPLACE INTO price_cache (code, price, currency, price_date, source, created_at)
           VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'))""",
        (code, price, currency, price_date, source),
    )
    await db.commit()
    return await get_latest_price(code)


async def update_price_currency(code: str, currency: str) -> None:
    """批量更新某标的全部历史价格的币种标签。"""
    db = await get_db()
    await db.execute(
        "UPDATE price_cache SET currency = ? WHERE code = ?",
        (currency, code),
    )
    await db.commit()


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


async def get_rates_in_range(pair: str, start_date: str, end_date: str) -> dict[str, float]:
    """批量获取指定日期范围的汇率，返回 {rate_date: rate}"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT rate_date, rate FROM exchange_rates WHERE pair = ? AND rate_date BETWEEN ? AND ?",
        (pair, start_date, end_date),
    )
    rows = await cursor.fetchall()
    return {row["rate_date"]: row["rate"] for row in rows}


async def get_price_history(code: str) -> list[dict]:
    """获取某标的完整价格历史，按日期升序"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM price_cache WHERE code = ? ORDER BY price_date ASC",
        (code,),
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


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
