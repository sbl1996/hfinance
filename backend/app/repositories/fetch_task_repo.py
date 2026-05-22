"""自动拉取任务 Repository"""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.db.connection import get_db
from app.models.schemas import FetchTaskCreate, FetchTaskUpdate

settings = get_settings()
APP_TZ = ZoneInfo(settings.APP_TIMEZONE)


def weekdays_to_mask(weekdays: list[int]) -> int:
    mask = 0
    for day in weekdays:
        if 0 <= day <= 6:
            mask |= 1 << day
    return mask


def mask_to_weekdays(mask: int) -> list[int]:
    return [day for day in range(7) if mask & (1 << day)]


async def list_tasks() -> list[dict]:
    db = await get_db()
    cursor = await db.execute(
        """
        SELECT
            ft.*,
            ftr.id AS latest_run_id,
            ftr.scheduled_for AS latest_run_scheduled_for,
            ftr.status AS latest_run_status,
            ftr.started_at AS latest_run_started_at,
            ftr.finished_at AS latest_run_finished_at,
            ftr.error_message AS latest_run_error_message,
            ftr.price_date AS latest_run_price_date,
            ftr.price_value AS latest_run_price_value
        FROM fetch_tasks ft
        LEFT JOIN fetch_task_runs ftr
          ON ftr.id = (
            SELECT id
            FROM fetch_task_runs
            WHERE task_id = ft.id
            ORDER BY scheduled_for DESC, id DESC
            LIMIT 1
          )
        ORDER BY ft.run_time ASC, ft.id ASC
        """
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def get_by_id(task_id: int) -> dict | None:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM fetch_tasks WHERE id = ?", (task_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def get_due_tasks(now: datetime) -> list[dict]:
    db = await get_db()
    run_time = now.strftime("%H:%M")
    weekday = now.weekday()
    cursor = await db.execute(
        """
        SELECT *
        FROM fetch_tasks
        WHERE enabled = 1
          AND run_time = ?
          AND (weekdays_mask & ?) != 0
        ORDER BY id ASC
        """,
        (run_time, 1 << weekday),
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def create_task(data: FetchTaskCreate) -> dict:
    db = await get_db()
    weekdays_mask = weekdays_to_mask(data.weekdays)
    cursor = await db.execute(
        """
        INSERT INTO fetch_tasks (code, name, market, enabled, run_time, weekdays_mask)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            data.code,
            data.name,
            data.market.value,
            1 if data.enabled else 0,
            data.run_time,
            weekdays_mask,
        ),
    )
    await db.commit()
    return await get_by_id(cursor.lastrowid)


async def update_task(task_id: int, data: FetchTaskUpdate) -> dict | None:
    existing = await get_by_id(task_id)
    if not existing:
        return None

    updates = data.model_dump(exclude_none=True)
    if not updates:
        return existing
    if "market" in updates:
        updates["market"] = updates["market"].value
    if "weekdays" in updates:
        updates["weekdays_mask"] = weekdays_to_mask(updates.pop("weekdays"))
    if "enabled" in updates:
        updates["enabled"] = 1 if updates["enabled"] else 0
    updates["updated_at"] = datetime.now(APP_TZ).strftime("%Y-%m-%d %H:%M:%S")

    set_clause = ", ".join(f"{key} = ?" for key in updates.keys())
    values = list(updates.values()) + [task_id]
    db = await get_db()
    await db.execute(f"UPDATE fetch_tasks SET {set_clause} WHERE id = ?", values)
    await db.commit()
    return await get_by_id(task_id)


async def delete_task(task_id: int) -> bool:
    db = await get_db()
    cursor = await db.execute("DELETE FROM fetch_tasks WHERE id = ?", (task_id,))
    await db.commit()
    return cursor.rowcount > 0
