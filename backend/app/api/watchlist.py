"""观察标的 API"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import WatchlistItemCreate, WatchlistItemListOut, WatchlistItemOut, CurrencyType
from app.repositories import price_repo, watchlist_repo

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


@router.delete("/{item_id}")
async def delete_watchlist_item(item_id: int):
    success = await watchlist_repo.delete(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="观察标的不存在")
    return {"detail": "删除成功"}
