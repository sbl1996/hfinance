"""自动拉取任务执行记录 Repository"""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.db.connection import get_db

settings = get_settings()
APP_TZ = ZoneInfo(settings.APP_TIMEZONE)


def _now_str() -> str:
    return datetime.now(APP_TZ).strftime("%Y-%m-%d %H:%M:%S")


async def get_active_run_for_task(task_id: int) -> dict | None:
    db = await get_db()
    cursor = await db.execute(
        """
        SELECT *
        FROM fetch_task_runs
        WHERE task_id = ?
          AND status IN ('PENDING', 'RUNNING')
        ORDER BY scheduled_for DESC, id DESC
        LIMIT 1
        """,
        (task_id,),
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def enqueue_task_run(task: dict, scheduled_for: str) -> bool:
    db = await get_db()
    cursor = await db.execute(
        """
        INSERT OR IGNORE INTO fetch_task_runs
            (task_id, code, name, market, scheduled_for, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 'PENDING', ?, ?)
        """,
        (
            task["id"],
            task["code"],
            task["name"],
            task["market"],
            scheduled_for,
            _now_str(),
            _now_str(),
        ),
    )
    await db.commit()
    return cursor.rowcount > 0


async def enqueue_manual_task_run(task: dict, scheduled_for: str) -> dict:
    db = await get_db()
    now = _now_str()
    cursor = await db.execute(
        """
        INSERT INTO fetch_task_runs
            (task_id, code, name, market, scheduled_for, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 'PENDING', ?, ?)
        RETURNING *
        """,
        (
            task["id"],
            task["code"],
            task["name"],
            task["market"],
            scheduled_for,
            now,
            now,
        ),
    )
    row = await cursor.fetchone()
    await db.commit()
    return dict(row)


async def claim_next_pending_run() -> dict | None:
    db = await get_db()
    cursor = await db.execute(
        """
        UPDATE fetch_task_runs
        SET status = 'RUNNING',
            started_at = ?,
            updated_at = ?
        WHERE id = (
            SELECT id
            FROM fetch_task_runs
            WHERE status = 'PENDING'
            ORDER BY scheduled_for ASC, id ASC
            LIMIT 1
        )
        RETURNING *
        """,
        (_now_str(), _now_str()),
    )
    row = await cursor.fetchone()
    await db.commit()
    return dict(row) if row else None


async def finish_run(
    run_id: int,
    *,
    status: str,
    error_message: str | None = None,
    price_date: str | None = None,
    price_value: float | None = None,
) -> None:
    db = await get_db()
    await db.execute(
        """
        UPDATE fetch_task_runs
        SET status = ?,
            finished_at = ?,
            error_message = ?,
            price_date = ?,
            price_value = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (status, _now_str(), error_message, price_date, price_value, _now_str(), run_id),
    )
    await db.commit()


async def list_runs_for_task(task_id: int, limit: int = 20) -> list[dict]:
    db = await get_db()
    cursor = await db.execute(
        """
        SELECT *
        FROM fetch_task_runs
        WHERE task_id = ?
        ORDER BY scheduled_for DESC, id DESC
        LIMIT ?
        """,
        (task_id, limit),
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def has_prior_fund_run_in_batch(*, scheduled_for: str, run_id: int) -> bool:
    db = await get_db()
    cursor = await db.execute(
        """
        SELECT 1
        FROM fetch_task_runs
        WHERE market = 'FUND'
          AND scheduled_for = ?
          AND id < ?
        LIMIT 1
        """,
        (scheduled_for, run_id),
    )
    return await cursor.fetchone() is not None


async def fail_running_runs_as_interrupted() -> None:
    db = await get_db()
    await db.execute(
        """
        UPDATE fetch_task_runs
        SET status = 'FAILED',
            finished_at = ?,
            error_message = '任务执行中断，服务已重启',
            updated_at = ?
        WHERE status = 'RUNNING'
        """,
        (_now_str(), _now_str()),
    )
    await db.commit()
