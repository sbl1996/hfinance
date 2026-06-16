"""
价格服务 - 遍历所有持仓，调用对应 fetcher，写入 price_cache 和 exchange_rates
支持降级逻辑：超时/报错时不写入缓存，保留旧数据
"""

import asyncio
import logging
import time

from app.repositories import holding_repo, price_repo, watchlist_repo
from app.services.market_fetcher import (
    fetch_a_etf,
    fetch_cny_fx_rates,
    fetch_cn_index,
    fetch_fund_nav,
    fetch_hk_stock,
    fetch_us_stock,
)

logger = logging.getLogger(__name__)

MARKET_SOURCE_GROUPS: dict[str, str] = {
    "HK_STOCK": "browser",
    "A_STOCK": "cn",
    "FUND": "fund",
    "US_STOCK": "us",
    "CN_INDEX": "browser",
}

SOURCE_GROUP_CONCURRENCY: dict[str, int] = {
    # Keep each source serialized first to avoid rate-limit regressions.
    "browser": 1,
    "cn": 1,
    "fund": 1,
    "us": 1,
}


async def _refresh_cny_fx_rates() -> None:
    """单次抓取并写入主要外汇兑人民币汇率。"""
    rate_results = fetch_cny_fx_rates()
    if rate_results:
        for pair, rate_result in rate_results.items():
            await price_repo.upsert_rate(
                pair=pair,
                rate=rate_result["rate"],
                rate_date=rate_result["rate_date"],
            )
        return

    reused_pairs: list[str] = []
    for pair in ("HKDCNY", "USDCNY"):
        old_rate = await price_repo.get_latest_rate(pair)
        if not old_rate:
            continue
        await price_repo.upsert_rate(
            pair=pair,
            rate=old_rate["rate"],
            rate_date=old_rate["rate_date"],
        )
        reused_pairs.append(pair)

    if reused_pairs:
        logger.warning("汇率获取失败，沿用上次缓存: %s", ", ".join(reused_pairs))


async def _resolve_fund_currency(code: str, fund_currency: str | None) -> str:
    if fund_currency:
        return fund_currency

    for item in [*(await holding_repo.get_all()), *(await watchlist_repo.get_all())]:
        if item["market"] == "FUND" and item["code"] == code:
            return item.get("currency") or "CNY"
    return "CNY"


async def _fetch_by_market(
    code: str,
    market: str,
    *,
    fund_currency: str | None = None,
    fund_force_refresh: bool = False,
) -> dict | None:
    """根据市场类型调用对应 fetcher"""
    if market == "HK_STOCK":
        return await asyncio.to_thread(fetch_hk_stock, code)
    elif market == "A_STOCK":
        return await asyncio.to_thread(fetch_a_etf, code)
    elif market == "FUND":
        resolved_currency = await _resolve_fund_currency(code, fund_currency)
        return await fetch_fund_nav(code, currency=resolved_currency, force_refresh=fund_force_refresh)
    elif market == "US_STOCK":
        return await asyncio.to_thread(fetch_us_stock, code)
    elif market == "CN_INDEX":
        return await asyncio.to_thread(fetch_cn_index, code)
    return None


async def execute_price_refresh(
    code: str,
    market: str,
    *,
    fund_currency: str | None = None,
    fund_force_refresh: bool = False,
) -> dict:
    """
    刷新单个标的的行情
    返回 {"code": str, "updated": bool, "price": float|None}
    """
    # 如果是港股，同时刷新汇率
    if market == "HK_STOCK":
        await _refresh_cny_fx_rates()

    result = None
    try:
        result = await _fetch_by_market(
            code,
            market,
            fund_currency=fund_currency,
            fund_force_refresh=fund_force_refresh,
        )
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


async def update_single_price(code: str, market: str, *, fund_currency: str | None = None) -> dict:
    return await execute_price_refresh(code, market, fund_currency=fund_currency)


def _get_source_group(market: str) -> str:
    return MARKET_SOURCE_GROUPS.get(market, market.lower())


async def _refresh_target(target: dict, *, fund_force_refresh: bool = False) -> dict:
    code = target["code"]
    market = target["market"]
    currency = target.get("currency")
    result = None
    previous_price = await price_repo.get_latest_price(code)

    try:
        result = await _fetch_by_market(
            code,
            market,
            fund_currency=currency,
            fund_force_refresh=fund_force_refresh,
        )
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
            "market": market,
            "source_group": _get_source_group(market),
            "updated": True,
            "failed": False,
            "price": result["price"],
            "price_date": result["price_date"],
            "previous_price_date": previous_price["price_date"] if previous_price else None,
        }

    logger.warning(f"标的 {code} 行情获取失败，保留旧缓存")
    return {
        "code": code,
        "market": market,
        "source_group": _get_source_group(market),
        "updated": False,
        "failed": True,
        "price": previous_price["price"] if previous_price else None,
        "price_date": previous_price["price_date"] if previous_price else None,
        "previous_price_date": previous_price["price_date"] if previous_price else None,
    }


async def _refresh_targets_in_group(
    source_group: str,
    targets: list[dict],
    *,
    fund_force_refresh: bool = False,
) -> dict:
    started_at = time.perf_counter()
    semaphore = asyncio.Semaphore(max(SOURCE_GROUP_CONCURRENCY.get(source_group, 1), 1))

    async def run_target(target: dict, *, force_refresh_fund: bool = False) -> dict:
        async with semaphore:
            return await _refresh_target(target, fund_force_refresh=force_refresh_fund)

    tasks = [
        run_target(
            target,
            force_refresh_fund=fund_force_refresh and source_group == "fund" and index == 0,
        )
        for index, target in enumerate(targets)
    ]
    results = await asyncio.gather(*tasks)

    return {
        "source_group": source_group,
        "updated": sum(1 for item in results if item["updated"]),
        "failed": sum(1 for item in results if item["failed"]),
        "elapsed_ms": int((time.perf_counter() - started_at) * 1000),
        "results": results,
    }


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

    if not targets:
        return {
            "updated": 0,
            "failed": 0,
            "is_trading_day": True,
        }

    requires_fx_refresh = any(
        target["market"] in {"HK_STOCK", "US_STOCK"}
        or (target["market"] == "FUND" and target.get("currency") in {"HKD", "USD"})
        for target in targets
    )
    if requires_fx_refresh:
        await _refresh_cny_fx_rates()

    grouped_targets: dict[str, list[dict]] = {}
    for target in targets:
        source_group = _get_source_group(target["market"])
        grouped_targets.setdefault(source_group, []).append(target)

    group_tasks = [
        _refresh_targets_in_group(
            source_group,
            group_targets,
            fund_force_refresh=market_type == "FUND",
        )
        for source_group, group_targets in grouped_targets.items()
    ]
    group_results = await asyncio.gather(*group_tasks)
    all_results = [item for group in group_results for item in group["results"]]

    updated = sum(group["updated"] for group in group_results)
    failed = sum(group["failed"] for group in group_results)

    # 判断是否交易日：用原始顺序中第一个成功刷新的港股或A股结果检查
    is_trading_day = True
    result_by_key = {(item["code"], item["market"]): item for item in all_results}
    for target in targets:
        if target["market"] not in {"HK_STOCK", "A_STOCK"}:
            continue
        result = result_by_key.get((target["code"], target["market"]))
        if not result or not result["updated"]:
            continue

        if result.get("previous_price_date") == result["price_date"]:
            is_trading_day = False
        break

    return {
        "updated": updated,
        "failed": failed,
        "is_trading_day": is_trading_day,
    }


def _merge_refresh_targets(holdings: list[dict], watchlist_items: list[dict]) -> list[dict]:
    merged: list[dict] = []
    seen: set[tuple[str, str]] = set()
    seen_fund_currency: dict[tuple[str, str], str] = {}
    for item in [*holdings, *watchlist_items]:
        key = (item["code"], item["market"])
        if item["market"] == "FUND":
            current_currency = item.get("currency") or "CNY"
            existing_currency = seen_fund_currency.get(key)
            if existing_currency and existing_currency != current_currency:
                logger.warning(
                    "基金 %s 存在不同币种配置，沿用首次出现的币种 %s，忽略 %s",
                    item["code"],
                    existing_currency,
                    current_currency,
                )
        if key in seen:
            continue
        seen.add(key)
        if item["market"] == "FUND":
            seen_fund_currency[key] = item.get("currency") or "CNY"
        merged.append({
            "code": item["code"],
            "market": item["market"],
            "currency": item.get("currency") if item["market"] == "FUND" else None,
        })
    return merged
