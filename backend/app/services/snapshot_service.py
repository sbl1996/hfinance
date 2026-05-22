"""
实时持仓指标服务

盈亏公式：(今日最新价 - 昨日收盘价) x 今日持仓数量 x 汇率

⚠️ Limitation：当用户在当日进行加仓/减仓操作时，由于使用「今日持仓数量」参与计算，
会导致当日盈亏出现轻微偏差（如昨日持有100股，今日加仓至200股，则价差盈亏会被放大）。
极简系统不引入流水账表，接受此小概率误差。
"""

import logging
from datetime import datetime

from app.repositories import holding_repo, price_repo

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
