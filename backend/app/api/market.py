"""行情刷新 API"""

from fastapi import APIRouter, HTTPException

from app.services.market_fetcher import invalidate_fund_nav_cache
from app.services.price_service import update_all_prices, update_single_price
from app.services.snapshot_service import calculate_daily_metrics

router = APIRouter()


@router.post("/refresh")
async def refresh_market():
    """手动触发全量行情更新，并返回实时计算的当日盈亏"""
    result = await update_all_prices()
    is_trading_day = result.get("is_trading_day", True)
    live_metrics = await calculate_daily_metrics(is_trading_day=is_trading_day)
    return {
        "price_update": result,
        "snapshot_date": None,
        "daily_pnl_cny": live_metrics["total_daily_pnl"] if live_metrics else 0,
    }


@router.post("/refresh/{code}")
async def refresh_single_market(code: str, market: str = "HK_STOCK"):
    """手动刷新单个标的的行情"""
    result = await update_single_price(code, market)
    if not result["updated"]:
        raise HTTPException(status_code=502, detail=f"标的 {code} 行情获取失败")
    return result


@router.post("/fund-nav-cache/invalidate")
async def invalidate_fund_daily_cache():
    """手动清空基金日净值总表缓存"""
    invalidate_fund_nav_cache()
    return {"ok": True}
