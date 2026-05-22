"""行情刷新 API"""

from fastapi import APIRouter, HTTPException

from app.services.market_fetcher import invalidate_fund_nav_cache
from app.services.price_service import update_all_prices, update_single_price

router = APIRouter()


@router.post("/refresh")
async def refresh_market():
    """手动触发全量行情更新"""
    result = await update_all_prices()
    return {"price_update": result}


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
