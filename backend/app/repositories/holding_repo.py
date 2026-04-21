"""持仓 CRUD Repository"""

from app.db.connection import get_db
from app.models.schemas import HoldingCreate, HoldingUpdate


async def get_all() -> list[dict]:
    db = await get_db()
    cursor = await db.execute(
        """
        SELECT h.*, hso.sort_order AS sort_order
        FROM holdings h
        INNER JOIN holding_sort_orders hso ON hso.holding_id = h.id
        ORDER BY hso.sort_order ASC, h.id ASC
        """
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def get_by_id(item_id: int) -> dict | None:
    db = await get_db()
    cursor = await db.execute(
        """
        SELECT h.*, hso.sort_order AS sort_order
        FROM holdings h
        INNER JOIN holding_sort_orders hso ON hso.holding_id = h.id
        WHERE h.id = ?
        """,
        (item_id,),
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def create(data: HoldingCreate) -> dict:
    db = await get_db()
    cursor = await db.execute("SELECT COALESCE(MAX(sort_order), 0) + 1 FROM holding_sort_orders")
    next_sort_order = (await cursor.fetchone())[0]
    cursor = await db.execute(
        "INSERT INTO holdings (code, name, market, quantity, cost_total_cny) VALUES (?, ?, ?, ?, ?)",
        (data.code, data.name, data.market.value, data.quantity, data.cost_total_cny),
    )
    await db.execute(
        "INSERT INTO holding_sort_orders (holding_id, sort_order) VALUES (?, ?)",
        (cursor.lastrowid, next_sort_order),
    )
    await db.commit()
    return await get_by_id(cursor.lastrowid)


async def update(item_id: int, data: HoldingUpdate) -> dict | None:
    existing = await get_by_id(item_id)
    if not existing:
        return None
    updates = data.model_dump(exclude_none=True)
    if not updates:
        return existing
    if "market" in updates:
        updates["market"] = updates["market"].value
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [item_id]
    db = await get_db()
    await db.execute(
        f"UPDATE holdings SET {set_clause}, updated_at = datetime('now', 'localtime') WHERE id = ?",
        values,
    )
    await db.commit()
    return await get_by_id(item_id)


async def delete(item_id: int) -> bool:
    db = await get_db()
    await db.execute("DELETE FROM holding_sort_orders WHERE holding_id = ?", (item_id,))
    cursor = await db.execute("DELETE FROM holdings WHERE id = ?", (item_id,))
    await db.commit()
    return cursor.rowcount > 0


async def reorder(items: list[dict]) -> None:
    db = await get_db()
    await db.execute("BEGIN")
    try:
        for item in items:
            await db.execute(
                """
                INSERT INTO holding_sort_orders (holding_id, sort_order, updated_at)
                VALUES (?, ?, datetime('now', 'localtime'))
                ON CONFLICT(holding_id) DO UPDATE SET
                    sort_order = excluded.sort_order,
                    updated_at = excluded.updated_at
                """,
                (item["id"], item["sort_order"]),
            )
            await db.execute(
                "UPDATE holdings SET updated_at = datetime('now', 'localtime') WHERE id = ?",
                (item["id"],),
            )
        await db.commit()
    except Exception:
        await db.rollback()
        raise
