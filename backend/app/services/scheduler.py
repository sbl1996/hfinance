"""
定时任务调度 - APScheduler
每天 16:30 自动执行 update_all_prices() + generate_daily_snapshot()
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import get_settings
from app.services.price_service import update_all_prices
from app.services.snapshot_service import generate_daily_snapshot

logger = logging.getLogger(__name__)
settings = get_settings()

scheduler = AsyncIOScheduler()


async def scheduled_price_update():
    """定时任务：更新价格 + 生成快照"""
    logger.info("定时任务开始：更新行情数据...")
    try:
        result = await update_all_prices()
        logger.info(f"行情更新完成: {result}")

        is_trading_day = result.get("is_trading_day", True)
        snapshot = await generate_daily_snapshot(is_trading_day=is_trading_day)
        if snapshot:
            logger.info(f"快照生成完成: {snapshot['snapshot_date']}")
        else:
            logger.info("无持仓，跳过快照生成")
    except Exception as e:
        logger.error(f"定时任务执行失败: {e}")


def start_scheduler():
    """启动定时任务调度器"""
    scheduler.add_job(
        scheduled_price_update,
        "cron",
        hour=settings.SCHEDULER_HOUR,
        minute=settings.SCHEDULER_MINUTE,
        id="price_update_job",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"定时任务已启动：每天 {settings.SCHEDULER_HOUR}:{settings.SCHEDULER_MINUTE:02d} 执行")
