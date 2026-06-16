"""货币与人民币换算辅助"""

from app.repositories import holding_repo, price_repo, watchlist_repo

RATE_PAIR_BY_CURRENCY: dict[str, str] = {
    "HKD": "HKDCNY",
    "USD": "USDCNY",
}


def get_rate_pair_for_currency(currency: str | None) -> str | None:
    if not currency:
        return None
    return RATE_PAIR_BY_CURRENCY.get(currency)


async def get_latest_cny_rate_map() -> dict[str, float]:
    rates = {"CNY": 1.0, "HKD": 1.0, "USD": 1.0}
    for currency, pair in RATE_PAIR_BY_CURRENCY.items():
        rate_data = await price_repo.get_latest_rate(pair)
        if rate_data:
            rates[currency] = float(rate_data["rate"])
    return rates


async def get_cny_rate_ranges(
    currencies: set[str],
    start_date: str,
    end_date: str,
) -> dict[str, dict[str, float]]:
    ranges: dict[str, dict[str, float]] = {}
    for currency in currencies:
        pair = get_rate_pair_for_currency(currency)
        if not pair:
            continue
        ranges[currency] = await price_repo.get_rates_in_range(pair, start_date, end_date)
    return ranges


def convert_amount_to_cny(
    amount: float,
    currency: str | None,
    rate_map: dict[str, float],
) -> float:
    return amount * rate_map.get(currency or "CNY", 1.0)


def get_cny_rate_for_date(
    currency: str | None,
    price_date: str,
    rate_ranges: dict[str, dict[str, float]],
    fallback_rate_map: dict[str, float] | None = None,
) -> float:
    if not currency or currency == "CNY":
        return 1.0
    date_rate = rate_ranges.get(currency, {}).get(price_date)
    if date_rate is not None:
        return date_rate
    if fallback_rate_map is not None:
        return fallback_rate_map.get(currency, 1.0)
    return 1.0


async def ensure_fund_currency_consistency(
    *,
    code: str,
    market: str,
    currency: str,
    exclude_holding_id: int | None = None,
    exclude_watchlist_id: int | None = None,
) -> None:
    if market != "FUND":
        return

    normalized_code = str(code).strip()
    normalized_currency = currency or "CNY"

    for holding in await holding_repo.get_all():
        if holding["id"] == exclude_holding_id:
            continue
        if holding["market"] != "FUND" or str(holding["code"]).strip() != normalized_code:
            continue
        existing_currency = holding.get("currency") or "CNY"
        if existing_currency != normalized_currency:
            raise ValueError(
                f"基金 {normalized_code} 已存在币种 {existing_currency}，不能再保存为 {normalized_currency}"
            )

    for item in await watchlist_repo.get_all():
        if item["id"] == exclude_watchlist_id:
            continue
        if item["market"] != "FUND" or str(item["code"]).strip() != normalized_code:
            continue
        existing_currency = item.get("currency") or "CNY"
        if existing_currency != normalized_currency:
            raise ValueError(
                f"基金 {normalized_code} 已存在币种 {existing_currency}，不能再保存为 {normalized_currency}"
            )
