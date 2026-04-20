"""现金账户 CRUD Repository"""

from app.db.connection import get_db
from app.models.schemas import CashAccountCreate, CashAccountUpdate


async def get_all() -> list[dict]:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM cash_accounts ORDER BY id")
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def get_by_id(item_id: int) -> dict | None:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM cash_accounts WHERE id = ?", (item_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def create(data: CashAccountCreate) -> dict:
    db = await get_db()
    cursor = await db.execute(
        "INSERT INTO cash_accounts (name, balance_cny, type) VALUES (?, ?, ?)",
        (data.name, data.balance_cny, data.type.value),
    )
    await db.commit()
    return await get_by_id(cursor.lastrowid)


async def update(item_id: int, data: CashAccountUpdate) -> dict | None:
    existing = await get_by_id(item_id)
    if not existing:
        return None
    updates = data.model_dump(exclude_none=True)
    if not updates:
        return existing
    # 枚举值转为字符串
    if "type" in updates:
        updates["type"] = updates["type"].value
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [item_id]
    db = await get_db()
    await db.execute(
        f"UPDATE cash_accounts SET {set_clause}, updated_at = datetime('now', 'localtime') WHERE id = ?",
        values,
    )
    await db.commit()
    return await get_by_id(item_id)


async def delete(item_id: int) -> bool:
    db = await get_db()
    cursor = await db.execute("DELETE FROM cash_accounts WHERE id = ?", (item_id,))
    await db.commit()
    return cursor.rowcount > 0


async def get_total_balance() -> float:
    db = await get_db()
    cursor = await db.execute("SELECT COALESCE(SUM(balance_cny), 0) as total FROM cash_accounts")
    row = await cursor.fetchone()
    return row["total"] if row else 0.0
