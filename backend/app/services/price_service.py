"""
价格服务 - 遍历所有持仓，调用对应 fetcher，写入 price_cache 和 exchange_rates
支持降级逻辑：超时/报错时沿用上一交易日价格，标记 is_stale=True
"""

import logging
from datetime import datetime

from app.repositories import holding_repo, price_repo
from app.services.market_fetcher import fetch_a_etf, fetch_fund_nav, fetch_hk_stock, fetch_hkdcny_rate

logger = logging.getLogger(__name__)


def _fetch_by_market(code: str, market: str) -> dict | None:
    """根据市场类型调用对应 fetcher"""
    if market == "HK_STOCK":
        return fetch_hk_stock(code)
    elif market == "A_STOCK":
        return fetch_a_etf(code)
    elif market == "FUND":
        return fetch_fund_nav(code)
    return None


async def update_single_price(code: str, market: str) -> dict:
    """
    刷新单个标的的行情
    返回 {"code": str, "updated": bool, "price": float|None, "growth_rate": float}
    """
    # 如果是港股，同时刷新汇率
    if market == "HK_STOCK":
        rate_result = fetch_hkdcny_rate()
        if rate_result:
            await price_repo.upsert_rate(
                pair="HKDCNY",
                rate=rate_result["rate"],
                rate_date=rate_result["rate_date"],
            )

    result = None
    try:
        result = _fetch_by_market(code, market)
    except Exception as e:
        logger.error(f"抓取 {code} 行情异常: {e}")

    if result:
        await price_repo.upsert_price(
            code=code,
            price=result["price"],
            currency=result["currency"],
            price_date=result["price_date"],
            growth_rate=result.get("growth_rate", 0.0),
        )
        return {
            "code": code,
            "updated": True,
            "price": result["price"],
            "growth_rate": result.get("growth_rate", 0.0),
        }
    else:
        # 抓取失败，沿用旧价格并标记陈旧
        old_price = await price_repo.get_latest_price(code)
        if old_price:
            await price_repo.upsert_price(
                code=code,
                price=old_price["price"],
                currency=old_price["currency"],
                price_date=old_price["price_date"],
                growth_rate=old_price.get("growth_rate", 0.0),
                is_stale=True,
            )
        logger.warning(f"标的 {code} 行情获取失败，沿用旧缓存")
        return {
            "code": code,
            "updated": False,
            "price": old_price["price"] if old_price else None,
            "growth_rate": old_price.get("growth_rate", 0.0) if old_price else 0.0,
        }


async def update_all_prices() -> dict:
    """
    遍历所有持仓，更新价格缓存和汇率缓存
    返回 {"updated": int, "failed": int, "is_trading_day": bool}
    """
    holdings = await holding_repo.get_all()
    updated = 0
    failed = 0
    today = datetime.now().strftime("%Y-%m-%d")

    # 先更新汇率
    rate_result = fetch_hkdcny_rate()
    if rate_result:
        await price_repo.upsert_rate(
            pair="HKDCNY",
            rate=rate_result["rate"],
            rate_date=rate_result["rate_date"],
        )
    else:
        # 汇率获取失败，标记旧汇率
        old_rate = await price_repo.get_latest_rate("HKDCNY")
        if old_rate:
            await price_repo.upsert_rate(
                pair="HKDCNY",
                rate=old_rate["rate"],
                rate_date=old_rate["rate_date"],
            )
            logger.warning("汇率获取失败，沿用上次缓存")

    # 判断是否交易日：用第一个港股或A股的数据检查
    is_trading_day = True
    first_price_checked = False

    for h in holdings:
        code = h["code"]
        market = h["market"]
        result = None

        try:
            result = _fetch_by_market(code, market)
        except Exception as e:
            logger.error(f"抓取 {code} 行情异常: {e}")

        # 判断是否交易日（非交易日：抓取的 price_date 与上次相同）
        if result and not first_price_checked:
            old_price = await price_repo.get_latest_price(code)
            if old_price and old_price["price_date"] == result["price_date"]:
                is_trading_day = False
            first_price_checked = True

        if result:
            await price_repo.upsert_price(
                code=code,
                price=result["price"],
                currency=result["currency"],
                price_date=result["price_date"],
                growth_rate=result.get("growth_rate", 0.0),
            )
            updated += 1
        else:
            # 抓取失败，沿用旧价格并标记陈旧
            old_price = await price_repo.get_latest_price(code)
            if old_price:
                await price_repo.upsert_price(
                    code=code,
                    price=old_price["price"],
                    currency=old_price["currency"],
                    price_date=old_price["price_date"],
                    growth_rate=old_price.get("growth_rate", 0.0),
                    is_stale=True,
                )
            failed += 1
            logger.warning(f"标的 {code} 行情获取失败，沿用旧缓存")

    return {
        "updated": updated,
        "failed": failed,
        "is_trading_day": is_trading_day,
    }
