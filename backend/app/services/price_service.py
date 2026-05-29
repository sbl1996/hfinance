"""
价格服务 - 遍历所有持仓，调用对应 fetcher，写入 price_cache 和 exchange_rates
支持降级逻辑：超时/报错时不写入缓存，保留旧数据
"""

import logging

from app.repositories import holding_repo, price_repo, watchlist_repo
from app.services.market_fetcher import fetch_a_etf, fetch_fund_nav, fetch_hk_stock, fetch_hkdcny_rate, fetch_us_stock

logger = logging.getLogger(__name__)


async def _fetch_by_market(code: str, market: str, *, fund_force_refresh: bool = False) -> dict | None:
    """根据市场类型调用对应 fetcher"""
    if market == "HK_STOCK":
        return fetch_hk_stock(code)
    elif market == "A_STOCK":
        return fetch_a_etf(code)
    elif market == "FUND":
        return await fetch_fund_nav(code, force_refresh=fund_force_refresh)
    elif market == "US_STOCK":
        return fetch_us_stock(code)
    return None


async def execute_price_refresh(code: str, market: str, *, fund_force_refresh: bool = False) -> dict:
    """
    刷新单个标的的行情
    返回 {"code": str, "updated": bool, "price": float|None}
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
        result = await _fetch_by_market(code, market, fund_force_refresh=fund_force_refresh)
    except Exception as e:
        logger.error(f"抓取 {code} 行情异常: {e}")

    if result:
        await price_repo.upsert_price(
            code=code,
            price=result["price"],
            currency=result["currency"],
            price_date=result["price_date"],
        )
        return {
            "code": code,
            "updated": True,
            "price": result["price"],
            "price_date": result["price_date"],
        }
    else:
        # 抓取失败，不写入缓存，保留旧数据
        old_price = await price_repo.get_latest_price(code)
        logger.warning(f"标的 {code} 行情获取失败，保留旧缓存")
        return {
            "code": code,
            "updated": False,
            "price": old_price["price"] if old_price else None,
            "price_date": old_price["price_date"] if old_price else None,
        }


async def update_single_price(code: str, market: str) -> dict:
    return await execute_price_refresh(code, market)


async def update_all_prices(*, market_type: str | None = None) -> dict:
    """
    遍历所有持仓，更新价格缓存和汇率缓存，支持按市场类型过滤
    返回 {"updated": int, "failed": int, "is_trading_day": bool}
    """
    holdings = await holding_repo.get_all()
    watchlist_items = await watchlist_repo.get_all()
    targets = _merge_refresh_targets(holdings, watchlist_items)
    
    if market_type:
        targets = [t for t in targets if t["market"] == market_type]
        
    updated = 0
    failed = 0

    # 仅在未指定市场或需要刷新港股时更新汇率
    if not market_type or market_type == "HK_STOCK":
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

    for target in targets:
        code = target["code"]
        market = target["market"]
        result = None

        try:
            result = await _fetch_by_market(code, market)
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
            )
            updated += 1
        else:
            # 抓取失败，不写入缓存，保留旧数据
            old_price = await price_repo.get_latest_price(code)
            failed += 1
            logger.warning(f"标的 {code} 行情获取失败，保留旧缓存")

    return {
        "updated": updated,
        "failed": failed,
        "is_trading_day": is_trading_day,
    }


def _merge_refresh_targets(holdings: list[dict], watchlist_items: list[dict]) -> list[dict]:
    merged: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for item in [*holdings, *watchlist_items]:
        key = (item["code"], item["market"])
        if key in seen:
            continue
        seen.add(key)
        merged.append({"code": item["code"], "market": item["market"]})
    return merged
