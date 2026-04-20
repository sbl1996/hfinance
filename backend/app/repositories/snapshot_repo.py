"""每日快照 Repository"""

from app.db.connection import get_db


async def create_snapshot(
    snapshot_date: str,
    total_assets_cny: float,
    total_liabilities_cny: float,
    net_assets_cny: float,
    daily_pnl_cny: float,
) -> dict:
    """创建每日快照（如果已存在则更新）"""
    db = await get_db()
    await db.execute(
        """INSERT OR REPLACE INTO daily_snapshots
           (snapshot_date, total_assets_cny, total_liabilities_cny, net_assets_cny, daily_pnl_cny, created_at)
           VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'))""",
        (snapshot_date, total_assets_cny, total_liabilities_cny, net_assets_cny, daily_pnl_cny),
    )
    await db.commit()
    cursor = await db.execute(
        "SELECT * FROM daily_snapshots WHERE snapshot_date = ?", (snapshot_date,)
    )
    row = await cursor.fetchone()
    return dict(row)


async def create_holding_snapshot(
    snapshot_id: int,
    holding_id: int,
    code: str,
    name: str,
    quantity: float,
    price: float,
    currency: str,
    market_value_cny: float,
    daily_pnl_cny: float,
) -> None:
    """创建持仓日快照"""
    db = await get_db()
    await db.execute(
        """INSERT INTO daily_holding_snapshots
           (snapshot_id, holding_id, code, name, quantity, price, currency, market_value_cny, daily_pnl_cny, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))""",
        (snapshot_id, holding_id, code, name, quantity, price, currency, market_value_cny, daily_pnl_cny),
    )
    await db.commit()


async def get_snapshot_by_date(snapshot_date: str) -> dict | None:
    """获取指定日期的快照"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM daily_snapshots WHERE snapshot_date = ?", (snapshot_date,)
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def get_latest_snapshot() -> dict | None:
    """获取最新一天的快照"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM daily_snapshots ORDER BY snapshot_date DESC LIMIT 1"
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def get_holding_snapshots_by_date(snapshot_date: str) -> list[dict]:
    """获取指定日期的持仓快照明细"""
    db = await get_db()
    cursor = await db.execute(
        """SELECT dhs.* FROM daily_holding_snapshots dhs
           INNER JOIN daily_snapshots ds ON dhs.snapshot_id = ds.id
           WHERE ds.snapshot_date = ?
           ORDER BY dhs.id""",
        (snapshot_date,),
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def get_month_pnl(year: int, month: int) -> list[dict]:
    """获取指定月份每日盈亏数据"""
    db = await get_db()
    month_prefix = f"{year}-{month:02d}"
    cursor = await db.execute(
        """SELECT snapshot_date, daily_pnl_cny FROM daily_snapshots
           WHERE snapshot_date LIKE ? || '%'
           ORDER BY snapshot_date""",
        (month_prefix,),
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def delete_holding_snapshots_by_date(snapshot_date: str) -> None:
    """删除指定日期的持仓快照（用于重新生成）"""
    db = await get_db()
    snapshot = await get_snapshot_by_date(snapshot_date)
    if snapshot:
        await db.execute(
            "DELETE FROM daily_holding_snapshots WHERE snapshot_id = ?",
            (snapshot["id"],),
        )
        await db.commit()
