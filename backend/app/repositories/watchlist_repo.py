"""自选标的 CRUD Repository"""

from app.db.connection import get_db
from app.models.schemas import WatchlistItemCreate, WatchlistItemUpdate


async def get_all() -> list[dict]:
    db = await get_db()
    cursor = await db.execute(
        """
        SELECT *
        FROM watchlist_items
        ORDER BY sort_order ASC, id ASC
        """
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def get_by_id(item_id: int) -> dict | None:
    db = await get_db()
    cursor = await db.execute(
        """
        SELECT *
        FROM watchlist_items
        WHERE id = ?
        """,
        (item_id,),
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def create(data: WatchlistItemCreate) -> dict:
    db = await get_db()
    cursor = await db.execute("SELECT COALESCE(MAX(sort_order), -1) + 1 FROM watchlist_items")
    next_sort_order = (await cursor.fetchone())[0]
    cursor = await db.execute(
        """
        INSERT INTO watchlist_items (code, name, market, currency, sort_order)
        VALUES (?, ?, ?, ?, ?)
        """,
        (data.code, data.name, data.market.value, data.currency.value, next_sort_order),
    )
    await db.commit()
    return await get_by_id(cursor.lastrowid)


async def update(item_id: int, data: WatchlistItemUpdate) -> dict | None:
    existing = await get_by_id(item_id)
    if not existing:
        return None

    updates = data.model_dump(exclude_none=True)
    if not updates:
        return existing
    if "market" in updates:
        updates["market"] = updates["market"].value
    if "currency" in updates:
        updates["currency"] = updates["currency"].value

    set_clause = ", ".join(f"{field} = ?" for field in updates)
    values = list(updates.values()) + [item_id]
    db = await get_db()
    await db.execute(
        f"UPDATE watchlist_items SET {set_clause}, updated_at = datetime('now', 'localtime') WHERE id = ?",
        values,
    )
    await db.commit()
    return await get_by_id(item_id)


async def delete(item_id: int) -> bool:
    db = await get_db()
    cursor = await db.execute("DELETE FROM watchlist_items WHERE id = ?", (item_id,))
    await db.commit()
    return cursor.rowcount > 0
