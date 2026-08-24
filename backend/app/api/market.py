"""行情刷新 API"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import RoutePoliciesOut, RoutePoliciesUpdate
from app.services.market_fetcher import invalidate_fund_nav_cache
from app.services.network_proxy_state import get_route_policies, set_route_policies, VPN_PROXY_URL
from app.services.price_service import update_all_prices, update_single_price

router = APIRouter()


@router.get("/route-policies", response_model=RoutePoliciesOut)
async def read_route_policies():
    return RoutePoliciesOut(policies=get_route_policies(), proxy_url=VPN_PROXY_URL)


@router.put("/route-policies", response_model=RoutePoliciesOut)
async def update_route_policies(data: RoutePoliciesUpdate):
    try:
        policies = await set_route_policies(data.policies)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RoutePoliciesOut(policies=policies, proxy_url=VPN_PROXY_URL)


@router.post("/refresh")
async def refresh_market(market: str | None = None):
    """手动触发行情更新，支持按市场类型过滤"""
    result = await update_all_prices(market_type=market)
    return {"price_update": result}


@router.post("/refresh/single")
async def refresh_single_market_query(code: str, market: str = "HK_STOCK", currency: str | None = None):
    """手动刷新单个标的的行情（query 参数形式，避免 path 中的 . 被反向代理拦截）"""
    result = await update_single_price(code, market, fund_currency=currency)
    if not result["updated"]:
        raise HTTPException(status_code=502, detail=f"标的 {code} 行情获取失败")
    return result


@router.post("/refresh/{code}")
async def refresh_single_market(code: str, market: str = "HK_STOCK", currency: str | None = None):
    """手动刷新单个标的的行情（兼容旧 path 参数形式）"""
    result = await update_single_price(code, market, fund_currency=currency)
    if not result["updated"]:
        raise HTTPException(status_code=502, detail=f"标的 {code} 行情获取失败")
    return result


@router.post("/fund-nav-cache/invalidate")
async def invalidate_fund_daily_cache():
    """手动清空基金日净值总表缓存"""
    invalidate_fund_nav_cache()
    return {"ok": True}
