"""持仓 API"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    HoldingCreate, HoldingOut, HoldingUpdate, HoldingListOut,
    CurrencyType, MarketType,
)
from app.repositories import holding_repo, price_repo, snapshot_repo

router = APIRouter()


async def _enrich_holding(h: dict) -> HoldingOut:
    """为持仓记录补充最新价、市值、盈亏等动态计算字段"""
    out = HoldingOut(**h)

    # 获取最新价格缓存
    price_data = await price_repo.get_latest_price(h["code"])
    rate_data = await price_repo.get_latest_rate("HKDCNY")

    hkdcny_rate = rate_data["rate"] if rate_data else 1.0
    out.hkdcny_rate = hkdcny_rate

    if price_data:
        out.latest_price = price_data["price"]
        out.price_currency = CurrencyType(price_data["currency"])
        out.price_date = price_data["price_date"]
        out.growth_rate = price_data.get("growth_rate", 0.0)
        out.is_stale = bool(price_data.get("is_stale", 0))

        # 计算市值(CNY)
        if h["market"] == MarketType.HK_STOCK.value:
            # 港股市值 = 港股价格 × 数量 × HKD/CNY汇率
            out.market_value_cny = price_data["price"] * h["quantity"] * hkdcny_rate
        else:
            # A股/基金市值 = 价格 × 数量
            out.market_value_cny = price_data["price"] * h["quantity"]

        # 计算盈亏
        out.pnl_cny = out.market_value_cny - h["cost_total_cny"]
        if h["cost_total_cny"] > 0:
            out.pnl_rate = out.pnl_cny / h["cost_total_cny"]
    else:
        out.is_stale = True

    return out


@router.get("", response_model=HoldingListOut)
async def list_holdings():
    """获取所有持仓列表（含最新价、市值CNY、收益率计算）"""
    items = await holding_repo.get_all()
    enriched = []
    total_mv = 0.0
    total_cost = 0.0
    total_pnl = 0.0
    for h in items:
        e = await _enrich_holding(h)
        enriched.append(e)
        if e.market_value_cny is not None:
            total_mv += e.market_value_cny
        total_cost += h["cost_total_cny"]
        if e.pnl_cny is not None:
            total_pnl += e.pnl_cny

    # 今日盈亏取最新快照
    latest_snapshot = await snapshot_repo.get_latest_snapshot()
    daily_pnl = latest_snapshot["daily_pnl_cny"] if latest_snapshot else 0.0

    return HoldingListOut(
        items=enriched,
        total_market_value_cny=total_mv,
        total_cost_cny=total_cost,
        total_pnl_cny=total_pnl,
        daily_pnl_cny=round(daily_pnl, 2),
    )


@router.post("", response_model=HoldingOut)
async def create_holding(data: HoldingCreate):
    """新增持仓"""
    item = await holding_repo.create(data)
    return await _enrich_holding(item)


@router.put("/{item_id}", response_model=HoldingOut)
async def update_holding(item_id: int, data: HoldingUpdate):
    """修改持仓"""
    item = await holding_repo.update(item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="持仓不存在")
    return await _enrich_holding(item)


@router.delete("/{item_id}")
async def delete_holding(item_id: int):
    """删除持仓"""
    success = await holding_repo.delete(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="持仓不存在")
    return {"detail": "删除成功"}
