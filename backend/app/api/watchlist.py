"""观察标的 API"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    CurrencyType,
    MarketType,
    WatchlistItemCreate,
    WatchlistItemListOut,
    WatchlistItemOut,
    WatchlistItemUpdate,
)
from app.repositories import price_repo, watchlist_repo
from app.services.fund_history_import_service import import_fund_history

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
        raise HTTPException(status_code=404, detail="观察标的不存在")
    return await _enrich_watchlist_item(item)


@router.put("/{item_id}", response_model=WatchlistItemOut)
async def update_watchlist_item(item_id: int, data: WatchlistItemUpdate):
    item = await watchlist_repo.update(item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="观察标的不存在")
    return await _enrich_watchlist_item(item)


@router.delete("/{item_id}")
async def delete_watchlist_item(item_id: int):
    success = await watchlist_repo.delete(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="观察标的不存在")
    return {"detail": "删除成功"}


@router.post("/{item_id}/import-history")
async def import_watchlist_history(item_id: int):
    item = await watchlist_repo.get_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="观察标的不存在")
    if item["market"] != MarketType.FUND.value:
        raise HTTPException(status_code=400, detail="只有基金观察标的支持全量导入")

    try:
        result = await import_fund_history(code=item["code"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"全量导入失败: {exc}") from exc

    return {
        "detail": f"已导入 {result['inserted']} 条净值记录",
        **result,
    }
