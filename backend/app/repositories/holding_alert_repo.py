"""持仓止盈止损预警设置 Repository。"""

from app.db.connection import get_db
from app.models.schemas import HoldingAlertUpdate


def _default_alert(holding_id: int) -> dict:
    return {
        "holding_id": holding_id,
        "enabled": 0,
        "take_profit_rate": None,
        "stop_loss_rate": None,
        "warning_active": 0,
        "warning_type": None,
        "warning_triggered_at": None,
        "last_trigger_date": None,
        "last_webhook_status": None,
        "last_webhook_error": None,
    }


async def get_by_holding_id(holding_id: int) -> dict:
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM holding_alert_settings WHERE holding_id = ?",
        (holding_id,),
    )
    row = await cursor.fetchone()
    return dict(row) if row else _default_alert(holding_id)


async def upsert(holding_id: int, data: HoldingAlertUpdate) -> dict:
    db = await get_db()
    await db.execute(
        """
        INSERT INTO holding_alert_settings (
            holding_id, enabled, take_profit_rate, stop_loss_rate,
            warning_active, warning_type, warning_triggered_at, last_trigger_date,
            last_webhook_status, last_webhook_error
        ) VALUES (?, ?, ?, ?, 0, NULL, NULL, NULL, NULL, NULL)
        ON CONFLICT(holding_id) DO UPDATE SET
            enabled = excluded.enabled,
            take_profit_rate = excluded.take_profit_rate,
            stop_loss_rate = excluded.stop_loss_rate,
            warning_active = 0,
            warning_type = NULL,
            warning_triggered_at = NULL,
            last_trigger_date = NULL,
            last_webhook_status = NULL,
            last_webhook_error = NULL,
            updated_at = datetime('now', 'localtime')
        """,
        (
            holding_id,
            1 if data.enabled else 0,
            data.take_profit_rate,
            data.stop_loss_rate,
        ),
    )
    await db.commit()
    return await get_by_holding_id(holding_id)


async def acknowledge(holding_id: int) -> dict:
    db = await get_db()
    await db.execute(
        """
        UPDATE holding_alert_settings
        SET warning_active = 0,
            warning_type = NULL,
            warning_triggered_at = NULL,
            updated_at = datetime('now', 'localtime')
        WHERE holding_id = ?
        """,
        (holding_id,),
    )
    await db.commit()
    return await get_by_holding_id(holding_id)


async def reset(holding_id: int) -> dict:
    db = await get_db()
    await db.execute(
        """
        UPDATE holding_alert_settings
        SET warning_active = 0,
            warning_type = NULL,
            warning_triggered_at = NULL,
            last_trigger_date = NULL,
            last_webhook_status = NULL,
            last_webhook_error = NULL,
            updated_at = datetime('now', 'localtime')
        WHERE holding_id = ?
        """,
        (holding_id,),
    )
    await db.commit()
    return await get_by_holding_id(holding_id)


async def activate_once_for_date(
    holding_id: int,
    warning_type: str,
    triggered_at: str,
    trigger_date: str,
) -> bool:
    """条件更新保证同一持仓同一天最多触发一次。"""
    db = await get_db()
    cursor = await db.execute(
        """
        UPDATE holding_alert_settings
        SET warning_active = 1,
            warning_type = ?,
            warning_triggered_at = ?,
            last_trigger_date = ?,
            last_webhook_status = NULL,
            last_webhook_error = NULL,
            updated_at = datetime('now', 'localtime')
        WHERE holding_id = ?
          AND enabled = 1
          AND warning_active = 0
          AND (last_trigger_date IS NULL OR last_trigger_date <> ?)
        """,
        (warning_type, triggered_at, trigger_date, holding_id, trigger_date),
    )
    await db.commit()
    return cursor.rowcount == 1


async def update_webhook_result(
    holding_id: int,
    status: str,
    error: str | None = None,
) -> None:
    db = await get_db()
    await db.execute(
        """
        UPDATE holding_alert_settings
        SET last_webhook_status = ?,
            last_webhook_error = ?,
            updated_at = datetime('now', 'localtime')
        WHERE holding_id = ?
        """,
        (status, error, holding_id),
    )
    await db.commit()
