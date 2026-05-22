"""
定时任务调度 - APScheduler
扫描应执行的自动拉取任务，并顺序消费执行队列
"""

import logging
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import get_settings
from app.services.fetch_task_service import consume_next_run, enqueue_due_tasks, recover_interrupted_runs

logger = logging.getLogger(__name__)
settings = get_settings()

scheduler = AsyncIOScheduler(timezone=ZoneInfo(settings.APP_TIMEZONE))


async def scheduled_enqueue_due_tasks():
    """扫描当前分钟应触发的任务并入队"""
    try:
        await enqueue_due_tasks()
    except Exception as exc:
        logger.error("自动拉取任务入队失败: %s", exc)


async def scheduled_consume_fetch_queue():
    """按队列顺序消费任务，严格串行"""
    try:
        await consume_next_run()
    except Exception as exc:
        logger.error("自动拉取任务消费失败: %s", exc)


async def start_scheduler():
    """启动定时任务调度器"""
    await recover_interrupted_runs()
    if scheduler.running:
        return

    scheduler.add_job(
        scheduled_enqueue_due_tasks,
        "cron",
        second=0,
        id="fetch_task_enqueue_job",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=30,
    )
    scheduler.add_job(
        scheduled_consume_fetch_queue,
        "interval",
        seconds=settings.FETCH_QUEUE_POLL_SECONDS,
        id="fetch_task_consume_job",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=max(settings.FETCH_QUEUE_POLL_SECONDS, 1),
    )
    scheduler.start()
    logger.info(
        "自动拉取调度已启动：timezone=%s enqueue=每分钟 queue_poll=%ss",
        settings.APP_TIMEZONE,
        settings.FETCH_QUEUE_POLL_SECONDS,
    )
