"""
快照服务 - 计算今日盈亏并写入 daily_snapshots 和 daily_holding_snapshots

盈亏公式：(今日最新价 - 昨日收盘价) x 今日持仓数量 x 汇率

⚠️ Limitation：当用户在当日进行加仓/减仓操作时，由于使用「今日持仓数量」参与计算，
会导致当日盈亏快照出现轻微偏差（如昨日持有100股，今日加仓至200股，则价差盈亏会被放大）。
极简系统不引入流水账表，接受此小概率误差。
"""

import logging
from datetime import datetime

from app.repositories import holding_repo, price_repo, snapshot_repo

logger = logging.getLogger(__name__)


async def generate_daily_snapshot(is_trading_day: bool = True) -> dict | None:
    """
    生成每日快照
    :param is_trading_day: 是否交易日（非交易日 daily_pnl 直接记为 0）
    :return: 快照字典 或 None
    """
    today = datetime.now().strftime("%Y-%m-%d")
    holdings = await holding_repo.get_all()

    if not holdings:
        logger.info("无持仓，跳过快照生成")
        return None

    # 获取汇率
    rate_data = await price_repo.get_latest_rate("HKDCNY")
    hkdcny_rate = rate_data["rate"] if rate_data else 1.0

    # 获取昨日快照（用于计算今日盈亏）
    # 取所有快照日期小于今天的最新一条
    yesterday_snapshot = None
    all_snapshots = await _get_snapshots_before_date(today)
    if all_snapshots:
        yesterday_snapshot = all_snapshots[-1]

    total_daily_pnl = 0.0
    total_market_value = 0.0

    # 先删除今日已有的持仓快照（允许重新生成）
    await snapshot_repo.delete_holding_snapshots_by_date(today)

    # 如果快照已存在，获取其 id；否则稍后创建
    existing_snapshot = await snapshot_repo.get_snapshot_by_date(today)

    for h in holdings:
        code = h["code"]
        market = h["market"]
        quantity = h["quantity"]

        # 获取今日价格
        today_price_data = await price_repo.get_latest_price(code)
        if not today_price_data:
            logger.warning(f"标的 {code} 无价格缓存，跳过快照")
            continue

        today_price = today_price_data["price"]
        currency = today_price_data["currency"]

        # 计算市值(CNY)
        if market == "HK_STOCK":
            market_value_cny = today_price * quantity * hkdcny_rate
        else:
            market_value_cny = today_price * quantity

        total_market_value += market_value_cny

        # 计算今日盈亏
        daily_pnl = 0.0
        if is_trading_day:
            # 尝试获取昨日价格
            yesterday_price = await _get_yesterday_price(code, today)
            if yesterday_price is not None:
                # ⚠️ Limitation: 使用今日持仓数量，当日内调仓会导致偏差
                if market == "HK_STOCK":
                    daily_pnl = (today_price - yesterday_price) * quantity * hkdcny_rate
                else:
                    daily_pnl = (today_price - yesterday_price) * quantity

        total_daily_pnl += daily_pnl

    # 获取现金和负债总额
    from app.repositories import cash_repo, liability_repo
    total_cash = await cash_repo.get_total_balance()
    total_liabilities = await liability_repo.get_total_amount()
    total_assets = total_cash + total_market_value
    net_assets = total_assets - total_liabilities

    # 非交易日盈亏为 0
    if not is_trading_day:
        total_daily_pnl = 0.0

    # 创建或更新快照
    snapshot = await snapshot_repo.create_snapshot(
        snapshot_date=today,
        total_assets_cny=round(total_assets, 2),
        total_liabilities_cny=round(total_liabilities, 2),
        net_assets_cny=round(net_assets, 2),
        daily_pnl_cny=round(total_daily_pnl, 2),
    )

    # 写入持仓快照明细
    for h in holdings:
        code = h["code"]
        market = h["market"]
        quantity = h["quantity"]

        today_price_data = await price_repo.get_latest_price(code)
        if not today_price_data:
            continue

        today_price = today_price_data["price"]
        currency = today_price_data["currency"]

        if market == "HK_STOCK":
            market_value_cny = today_price * quantity * hkdcny_rate
        else:
            market_value_cny = today_price * quantity

        daily_pnl = 0.0
        if is_trading_day:
            yesterday_price = await _get_yesterday_price(code, today)
            if yesterday_price is not None:
                if market == "HK_STOCK":
                    daily_pnl = (today_price - yesterday_price) * quantity * hkdcny_rate
                else:
                    daily_pnl = (today_price - yesterday_price) * quantity

        if not is_trading_day:
            daily_pnl = 0.0

        await snapshot_repo.create_holding_snapshot(
            snapshot_id=snapshot["id"],
            holding_id=h["id"],
            code=code,
            name=h["name"],
            quantity=quantity,
            price=today_price,
            currency=currency,
            market_value_cny=round(market_value_cny, 2),
            daily_pnl_cny=round(daily_pnl, 2),
        )

    logger.info(f"快照生成完成: {today}, 今日盈亏={total_daily_pnl:.2f}")
    return snapshot


async def _get_yesterday_price(code: str, today: str) -> float | None:
    """获取标的在今日之前最近一次的价格"""
    # 直接从 price_cache 获取该标的的最新价格（即今日价格）
    # 但我们需要「昨日收盘价」，即上一个不同日期的价格
    from app.db.connection import get_db
    db = await get_db()
    cursor = await db.execute(
        """SELECT price FROM price_cache
           WHERE code = ? AND price_date < ?
           ORDER BY price_date DESC LIMIT 1""",
        (code, today),
    )
    row = await cursor.fetchone()
    return row["price"] if row else None


async def _get_snapshots_before_date(date_str: str) -> list[dict]:
    """获取指定日期之前的快照"""
    from app.db.connection import get_db
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM daily_snapshots WHERE snapshot_date < ? ORDER BY snapshot_date DESC LIMIT 1",
        (date_str,),
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]
