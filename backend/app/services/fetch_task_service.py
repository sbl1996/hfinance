"""自动拉取任务服务"""

import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.repositories import fetch_task_repo, fetch_task_run_repo
from app.services.price_service import execute_price_refresh

logger = logging.getLogger(__name__)
settings = get_settings()
APP_TZ = ZoneInfo(settings.APP_TIMEZONE)


class ActiveFetchTaskRunError(Exception):
    """Raised when a task already has a pending or running run."""

    def __init__(self, active_run: dict):
        self.active_run = active_run
        super().__init__("任务已在排队或执行中，请勿重复提交")


async def enqueue_due_tasks(now: datetime | None = None) -> dict:
    current = now or datetime.now(APP_TZ)
    scheduled_for = current.replace(second=0, microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
    due_tasks = await fetch_task_repo.get_due_tasks(current)
    inserted = 0
    for task in due_tasks:
        if await fetch_task_run_repo.enqueue_task_run(task, scheduled_for):
            inserted += 1
    if inserted:
        logger.info("已入队 %s 条自动拉取任务 @ %s", inserted, scheduled_for)
    return {"scheduled_for": scheduled_for, "matched": len(due_tasks), "enqueued": inserted}


async def enqueue_manual_run(task_id: int) -> dict | None:
    task = await fetch_task_repo.get_by_id(task_id)
    if not task:
        return None

    active_run = await fetch_task_run_repo.get_active_run_for_task(task_id)
    if active_run:
        raise ActiveFetchTaskRunError(active_run)

    scheduled_for = datetime.now(APP_TZ).strftime("%Y-%m-%d %H:%M:%S")
    return await fetch_task_run_repo.enqueue_manual_task_run(task, scheduled_for)


async def consume_next_run() -> dict | None:
    run = await fetch_task_run_repo.claim_next_pending_run()
    if not run:
        return None

    try:
        fund_force_refresh = False
        if run["market"] == "FUND":
            has_prior = await fetch_task_run_repo.has_prior_fund_run_in_batch(
                scheduled_for=run["scheduled_for"],
                run_id=run["id"],
            )
            fund_force_refresh = not has_prior

        result = await execute_price_refresh(
            run["code"],
            run["market"],
            fund_force_refresh=fund_force_refresh,
        )
        if result["updated"]:
            await fetch_task_run_repo.finish_run(
                run["id"],
                status="SUCCESS",
                price_date=result.get("price_date"),
                price_value=result.get("price"),
            )
        else:
            await fetch_task_run_repo.finish_run(
                run["id"],
                status="FAILED",
                error_message="拉取失败，已保留旧缓存",
                price_date=result.get("price_date"),
                price_value=result.get("price"),
            )

        if run["market"] == "FUND":
            await asyncio.sleep(1)

        return {"run_id": run["id"], "status": "SUCCESS" if result["updated"] else "FAILED"}
    except Exception as exc:
        logger.exception("执行自动拉取任务失败: run_id=%s", run["id"])
        await fetch_task_run_repo.finish_run(
            run["id"],
            status="FAILED",
            error_message=str(exc),
        )
        return {"run_id": run["id"], "status": "FAILED"}


async def recover_interrupted_runs() -> None:
    await fetch_task_run_repo.fail_running_runs_as_interrupted()
