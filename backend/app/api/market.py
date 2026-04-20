"""行情刷新 API"""

from fastapi import APIRouter, HTTPException

from app.services.price_service import update_all_prices, update_single_price
from app.services.snapshot_service import generate_daily_snapshot

router = APIRouter()


@router.post("/refresh")
async def refresh_market():
    """手动触发全量行情更新 + 快照生成"""
    result = await update_all_prices()
    is_trading_day = result.get("is_trading_day", True)
    snapshot = await generate_daily_snapshot(is_trading_day=is_trading_day)
    return {
        "price_update": result,
        "snapshot_date": snapshot["snapshot_date"] if snapshot else None,
        "daily_pnl_cny": snapshot["daily_pnl_cny"] if snapshot else 0,
    }


@router.post("/refresh/{code}")
async def refresh_single_market(code: str, market: str = "HK_STOCK"):
    """手动刷新单个标的的行情"""
    result = await update_single_price(code, market)
    if not result["updated"]:
        raise HTTPException(status_code=502, detail=f"标的 {code} 行情获取失败")
    return result
