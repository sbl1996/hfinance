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
