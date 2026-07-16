"""持仓 API"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    HoldingCreate, HoldingOut, HoldingUpdate, HoldingListOut,
    CurrencyType, MarketType, HoldingReorderRequest, HoldingIgnoreUpdate,
    PriceHistoryResponse, PriceHistoryItem,
)
from app.repositories import holding_repo, price_repo
from app.services.currency_service import (
    ensure_fund_currency_consistency,
    get_cny_rate_for_date,
    get_cny_rate_ranges,
    get_latest_cny_rate_map,
)
from app.services.fund_history_import_service import import_fund_history
from app.services.daily_metrics_service import calculate_daily_metrics

router = APIRouter()


async def _enrich_holding(h: dict) -> HoldingOut:
    """为持仓记录补充最新价、市值、盈亏等动态计算字段"""
    out = HoldingOut(**h)

    # 获取最新价格缓存
    price_data = await price_repo.get_latest_price(h["code"])
    latest_rate_map = await get_latest_cny_rate_map()
    hkdcny_rate = latest_rate_map["HKD"]
    out.hkdcny_rate = hkdcny_rate

    if price_data:
        out.latest_price = price_data["price"]
        out.price_currency = CurrencyType(price_data["currency"])
        out.price_date = price_data["price_date"]
        price_currency = str(price_data["currency"])
        cny_rate = latest_rate_map.get(price_currency, 1.0)

        # 动态计算涨跌幅：基于 price_cache 中最新价与前一日价格
        prev_price_data = await price_repo.get_previous_price(h["code"], price_data["price_date"])
        if prev_price_data and prev_price_data["price"] > 0:
            price_diff = price_data["price"] - prev_price_data["price"]
            out.growth_rate = price_diff / prev_price_data["price"]
            out.growth_pnl_cny = price_diff * h["quantity"] * cny_rate
        else:
            out.growth_rate = None
            out.growth_pnl_cny = None

        # 计算市值(CNY)
        out.market_value_cny = price_data["price"] * h["quantity"] * cny_rate

        # 计算盈亏
        out.pnl_cny = out.market_value_cny - h["cost_total_cny"]
        if h["cost_total_cny"] > 0:
            out.pnl_rate = out.pnl_cny / h["cost_total_cny"]

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
        if not e.ignored and e.pnl_cny is not None:
            total_pnl += e.pnl_cny

    live_metrics = await calculate_daily_metrics(is_trading_day=True)
    daily_pnl = live_metrics["total_daily_pnl"] if live_metrics else 0.0

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
    try:
        await ensure_fund_currency_consistency(
            code=data.code,
            market=data.market.value,
            currency=data.currency.value,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    item = await holding_repo.create(data)
    if item["market"] == MarketType.FUND.value:
        await price_repo.update_price_currency(item["code"], item.get("currency", "CNY"))
    return await _enrich_holding(item)


@router.put("/{item_id}", response_model=HoldingOut)
async def update_holding(item_id: int, data: HoldingUpdate):
    """修改持仓"""
    existing = await holding_repo.get_by_id(item_id)
    if not existing:
        raise HTTPException(status_code=404, detail="持仓不存在")

    next_code = data.code if data.code is not None else existing["code"]
    next_market = data.market.value if data.market is not None else existing["market"]
    next_currency = data.currency.value if data.currency is not None else existing.get("currency", "CNY")
    try:
        await ensure_fund_currency_consistency(
            code=next_code,
            market=next_market,
            currency=next_currency,
            exclude_holding_id=item_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    item = await holding_repo.update(item_id, data)
    if item["market"] == MarketType.FUND.value:
        await price_repo.update_price_currency(item["code"], item.get("currency", "CNY"))
    return await _enrich_holding(item)


@router.put("/{item_id}/ignored", response_model=HoldingOut)
async def update_holding_ignored(item_id: int, data: HoldingIgnoreUpdate):
    """更新持仓是否忽略盈亏统计"""
    item = await holding_repo.set_ignored(item_id, data.ignored)
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


@router.post("/reorder")
async def reorder_holdings(data: HoldingReorderRequest):
    """批量更新持仓排序"""
    existing_items = await holding_repo.get_all()
    existing_ids = {item["id"] for item in existing_items}
    request_ids = [item.id for item in data.items]

    if len(request_ids) != len(set(request_ids)):
        raise HTTPException(status_code=400, detail="排序请求包含重复持仓")
    if set(request_ids) != existing_ids:
        raise HTTPException(status_code=400, detail="排序请求必须包含全部持仓且不能包含未知持仓")

    await holding_repo.reorder([item.model_dump() for item in data.items])
    return {"detail": "排序已更新"}


@router.post("/{item_id}/import-history")
async def import_holding_history(item_id: int):
    """全量导入基金历史净值到 price_cache"""
    holding = await holding_repo.get_by_id(item_id)
    if not holding:
        raise HTTPException(status_code=404, detail="持仓不存在")
    if holding["market"] != MarketType.FUND.value:
        raise HTTPException(status_code=400, detail="只有基金持仓支持全量导入")

    try:
        result = await import_fund_history(code=holding["code"], currency=holding.get("currency", "CNY"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"全量导入失败: {exc}") from exc

    return {
        "detail": f"已导入 {result['inserted']} 条净值记录",
        **result,
    }


@router.get("/{item_id}/price_history", response_model=PriceHistoryResponse)
async def get_holding_price_history(item_id: int):
    """获取持仓标的价格历史（含收益率曲线数据）"""
    holding = await holding_repo.get_by_id(item_id)
    if not holding:
        raise HTTPException(status_code=404, detail="持仓不存在")

    enriched = await _enrich_holding(holding)

    unit_cost = 0.0
    if holding["quantity"] > 0:
        unit_cost = holding["cost_total_cny"] / holding["quantity"]

    # 成本原始录入口径是 CNY。对外币标的以最新汇率折算一份本币成本，
    # 方便与本币最新价比较；人民币成本仍保留给市值、盈亏和历史图表使用。
    unit_cost_native = None
    unit_cost_native_currency = None
    current_price_native = enriched.latest_price
    current_price_cny = None
    if enriched.latest_price is not None and enriched.price_currency is not None:
        price_currency = enriched.price_currency.value
        latest_rate_map = await get_latest_cny_rate_map()
        cny_rate = latest_rate_map.get(price_currency, 1.0)
        current_price_cny = enriched.latest_price * cny_rate
        if cny_rate > 0:
            unit_cost_native = unit_cost / cny_rate
            unit_cost_native_currency = enriched.price_currency

    raw_history = await price_repo.get_price_history(holding["code"])
    if not raw_history:
        return PriceHistoryResponse(
            code=holding["code"],
            name=holding["name"],
            unit_cost=unit_cost,
            market=MarketType(holding["market"]),
            currency=CurrencyType(holding.get("currency") or "CNY"),
            current_price=enriched.latest_price,
            current_price_native=current_price_native,
            current_price_cny=round(current_price_cny, 4) if current_price_cny is not None else None,
            price_currency=enriched.price_currency,
            unit_cost_native=round(unit_cost_native, 4) if unit_cost_native is not None else None,
            unit_cost_native_currency=unit_cost_native_currency,
            price_date=enriched.price_date,
            market_value_cny=enriched.market_value_cny,
            pnl_cny=enriched.pnl_cny,
            pnl_rate=enriched.pnl_rate,
            growth_rate=enriched.growth_rate,
            growth_pnl_cny=enriched.growth_pnl_cny,
            quantity=holding["quantity"],
            cost_total_cny=holding["cost_total_cny"],
            history=[],
            empty=True,
        )

    rate_ranges: dict[str, dict[str, float]] = {}
    fallback_rate_map = await get_latest_cny_rate_map()
    currencies = {str(record["currency"]) for record in raw_history if str(record["currency"]) != "CNY"}
    if currencies:
        start_date = raw_history[0]["price_date"]
        end_date = raw_history[-1]["price_date"]
        rate_ranges = await get_cny_rate_ranges(currencies, start_date, end_date)

    history = []
    for record in raw_history:
        price = record["price"]
        rate = get_cny_rate_for_date(
            str(record["currency"]),
            record["price_date"],
            rate_ranges,
            fallback_rate_map,
        )
        price = price * rate

        yield_rate = None
        if unit_cost > 0:
            yield_rate = (price - unit_cost) / unit_cost * 100

        history.append(PriceHistoryItem(
            date=record["price_date"],
            price=round(price, 4),
            yield_rate=round(yield_rate, 2) if yield_rate is not None else None,
        ))

    return PriceHistoryResponse(
        code=holding["code"],
        name=holding["name"],
        unit_cost=round(unit_cost, 4),
        market=MarketType(holding["market"]),
        currency=CurrencyType(holding.get("currency") or "CNY"),
        current_price=enriched.latest_price,
        current_price_native=current_price_native,
        current_price_cny=round(current_price_cny, 4) if current_price_cny is not None else None,
        price_currency=enriched.price_currency,
        unit_cost_native=round(unit_cost_native, 4) if unit_cost_native is not None else None,
        unit_cost_native_currency=unit_cost_native_currency,
        price_date=enriched.price_date,
        market_value_cny=enriched.market_value_cny,
        pnl_cny=enriched.pnl_cny,
        pnl_rate=enriched.pnl_rate,
        growth_rate=enriched.growth_rate,
        growth_pnl_cny=enriched.growth_pnl_cny,
        quantity=holding["quantity"],
        cost_total_cny=holding["cost_total_cny"],
        history=history,
        empty=False,
    )
