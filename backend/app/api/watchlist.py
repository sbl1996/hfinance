"""自选标的 API"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    CurrencyType,
    MarketType,
    WatchlistItemCreate,
    WatchlistItemListOut,
    WatchlistItemOut,
    WatchlistItemUpdate,
    PriceHistoryItem,
    WatchlistPriceHistoryResponse,
    WatchMarketType,
)
from app.repositories import price_repo, watchlist_repo
from app.services.fund_history_import_service import import_fund_history, import_us_stock_history

router = APIRouter()


async def _enrich_watchlist_item(item: dict) -> WatchlistItemOut:
    out = WatchlistItemOut(**item)
    price_data = await price_repo.get_latest_price(item["code"])
    if price_data:
        out.latest_price = price_data["price"]
        out.price_currency = CurrencyType(price_data["currency"])
        out.price_date = price_data["price_date"]

        previous_price = await price_repo.get_previous_price(item["code"], price_data["price_date"])
        if previous_price and previous_price["price"] > 0:
            out.growth_rate = (price_data["price"] - previous_price["price"]) / previous_price["price"]

    return out


@router.get("", response_model=WatchlistItemListOut)
async def list_watchlist():
    items = await watchlist_repo.get_all()
    enriched = [await _enrich_watchlist_item(item) for item in items]
    return WatchlistItemListOut(items=enriched)


@router.post("", response_model=WatchlistItemOut)
async def create_watchlist_item(data: WatchlistItemCreate):
    item = await watchlist_repo.create(data)
    return await _enrich_watchlist_item(item)


@router.get("/{item_id}", response_model=WatchlistItemOut)
async def get_watchlist_item(item_id: int):
    item = await watchlist_repo.get_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="自选标的不存在")
    return await _enrich_watchlist_item(item)


@router.put("/{item_id}", response_model=WatchlistItemOut)
async def update_watchlist_item(item_id: int, data: WatchlistItemUpdate):
    item = await watchlist_repo.update(item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="自选标的不存在")
    return await _enrich_watchlist_item(item)


@router.delete("/{item_id}")
async def delete_watchlist_item(item_id: int):
    success = await watchlist_repo.delete(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="自选标的不存在")
    return {"detail": "删除成功"}


@router.post("/{item_id}/import-history")
async def import_watchlist_history(item_id: int):
    item = await watchlist_repo.get_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="自选标的不存在")

    try:
        if item["market"] == MarketType.FUND.value:
            result = await import_fund_history(code=item["code"])
        elif item["market"] == "US_STOCK":
            result = await import_us_stock_history(code=item["code"])
        else:
            raise HTTPException(status_code=400, detail="只有基金和美股自选标的支持全量导入")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"全量导入失败: {exc}") from exc

    return {
        "detail": f"已导入 {result['inserted']} 条净值记录",
        **result,
    }


@router.get("/{item_id}/price_history", response_model=WatchlistPriceHistoryResponse)
async def get_watchlist_price_history(item_id: int):
    """获取自选标的价格历史"""
    item = await watchlist_repo.get_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="自选标的不存在")

    enriched = await _enrich_watchlist_item(item)

    raw_history = await price_repo.get_price_history(item["code"])
    if not raw_history:
        return WatchlistPriceHistoryResponse(
            id=enriched.id,
            code=enriched.code,
            name=enriched.name,
            market=enriched.market,
            latest_price=enriched.latest_price,
            current_price=enriched.latest_price,
            price_currency=enriched.price_currency,
            price_date=enriched.price_date,
            growth_rate=enriched.growth_rate,
            created_at=enriched.created_at,
            updated_at=enriched.updated_at,
            history=[],
            empty=True,
        )

    history = []
    for record in raw_history:
        history.append(PriceHistoryItem(
            date=record["price_date"],
            price=round(record["price"], 4),
            yield_rate=None,  # 自选标的无持有成本，不计算收益率
        ))

    return WatchlistPriceHistoryResponse(
        id=enriched.id,
        code=enriched.code,
        name=enriched.name,
        market=enriched.market,
        latest_price=enriched.latest_price,
        current_price=enriched.latest_price,
        price_currency=enriched.price_currency,
        price_date=enriched.price_date,
        growth_rate=enriched.growth_rate,
        created_at=enriched.created_at,
        updated_at=enriched.updated_at,
        history=history,
        empty=False,
    )
