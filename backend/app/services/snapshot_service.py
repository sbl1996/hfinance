"""
快照服务 - 计算今日盈亏并写入 daily_snapshots

盈亏公式：(今日最新价 - 昨日收盘价) x 今日持仓数量 x 汇率

⚠️ Limitation：当用户在当日进行加仓/减仓操作时，由于使用「今日持仓数量」参与计算，
会导致当日盈亏快照出现轻微偏差（如昨日持有100股，今日加仓至200股，则价差盈亏会被放大）。
极简系统不引入流水账表，接受此小概率误差。
"""

import logging
from datetime import datetime

from app.repositories import holding_repo, price_repo, snapshot_repo

logger = logging.getLogger(__name__)


async def calculate_daily_metrics(
    *,
    is_trading_day: bool = True,
) -> dict | None:
    """
    计算当前持仓的日盈亏与投资市值，不写入快照表。

    :param is_trading_day: 是否交易日（非交易日 daily_pnl 直接记为 0）
    :return: {"as_of_date": str, "total_daily_pnl": float, "total_market_value": float} 或 None
    """
    holdings = await holding_repo.get_all()
    if not holdings:
        logger.info("无持仓，跳过日盈亏计算")
        return None

    rate_data = await price_repo.get_latest_rate("HKDCNY")
    hkdcny_rate = rate_data["rate"] if rate_data else 1.0

    total_daily_pnl = 0.0
    total_market_value = 0.0
    as_of_date = None

    for h in holdings:
        code = h["code"]
        market = h["market"]
        quantity = h["quantity"]
        ignored = bool(h["ignored"])

        today_price_data = await price_repo.get_latest_price(code)
        if not today_price_data:
            logger.warning(f"标的 {code} 无价格缓存，跳过日盈亏计算")
            continue

        today_price = today_price_data["price"]
        price_date = today_price_data["price_date"]
        if as_of_date is None or price_date > as_of_date:
            as_of_date = price_date

        if market == "HK_STOCK":
            market_value_cny = today_price * quantity * hkdcny_rate
        else:
            market_value_cny = today_price * quantity
        total_market_value += market_value_cny

        daily_pnl = 0.0
        if is_trading_day and not ignored:
            # 以前一条实际缓存行情作为对比基准，避免缓存停留在历史日期时把“当前价”误当成“昨日价”
            previous_price_data = await price_repo.get_previous_price(code, price_date)
            if previous_price_data:
                previous_price = previous_price_data["price"]
                # ⚠️ Limitation: 使用今日持仓数量，当日内调仓会导致偏差
                if market == "HK_STOCK":
                    daily_pnl = (today_price - previous_price) * quantity * hkdcny_rate
                else:
                    daily_pnl = (today_price - previous_price) * quantity

        total_daily_pnl += daily_pnl

    return {
        "as_of_date": as_of_date or datetime.now().strftime("%Y-%m-%d"),
        "total_daily_pnl": round(0.0 if not is_trading_day else total_daily_pnl, 2),
        "total_market_value": round(total_market_value, 2),
    }


async def generate_daily_snapshot(is_trading_day: bool = True) -> dict | None:
    """
    生成每日快照
    :param is_trading_day: 是否交易日（非交易日 daily_pnl 直接记为 0）
    :return: 快照字典 或 None
    """
    today = datetime.now().strftime("%Y-%m-%d")
    metrics = await calculate_daily_metrics(is_trading_day=is_trading_day)
    if not metrics:
        return None
    total_daily_pnl = metrics["total_daily_pnl"]
    total_market_value = metrics["total_market_value"]

    # 获取现金和负债总额
    from app.repositories import cash_repo, liability_repo
    total_cash = await cash_repo.get_total_balance()
    total_liabilities = await liability_repo.get_total_amount()
    total_assets = total_cash + total_market_value
    net_assets = total_assets - total_liabilities

    # 创建或更新快照
    snapshot = await snapshot_repo.create_snapshot(
        snapshot_date=today,
        total_assets_cny=round(total_assets, 2),
        total_liabilities_cny=round(total_liabilities, 2),
        net_assets_cny=round(net_assets, 2),
        daily_pnl_cny=round(total_daily_pnl, 2),
    )

    logger.info(f"快照生成完成: {today}, 今日盈亏={total_daily_pnl:.2f}")
    return snapshot
