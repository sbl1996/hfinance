"""基金历史净值全量导入服务"""

import akshare as ak

from app.repositories import price_repo


def fetch_fund_history(code: str):
    df = ak.fund_open_fund_info_em(symbol=code)
    if df.empty:
        raise ValueError(f"基金 {code} 未获取到净值数据")
    return df


def load_daily_prices_from_dataframe(df) -> dict[str, float]:
    daily_prices: dict[str, float] = {}
    required_columns = {"净值日期", "单位净值"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(f"基金数据缺少必要列: {', '.join(sorted(missing_columns))}")

    for row_no, (_, row) in enumerate(df.iterrows(), start=2):
        date_str = str(row.get("净值日期") or "").strip()[:10]
        price_str = str(row.get("单位净值") or "").strip()
        if not date_str or not price_str or price_str.lower() == "nan":
            continue

        try:
            daily_prices[date_str] = float(price_str)
        except ValueError as exc:
            raise ValueError(f"第 {row_no} 行单位净值无法解析: {price_str}") from exc

    return daily_prices


async def import_fund_history(code: str, currency: str = "CNY", source: str = "ak_share") -> dict:
    df = fetch_fund_history(code)
    daily_prices = load_daily_prices_from_dataframe(df)
    if not daily_prices:
        raise ValueError("抓取结果中没有可导入的数据")

    sorted_dates = sorted(daily_prices.keys())
    inserted = 0
    for date_str in sorted_dates:
        await price_repo.upsert_price(
            code=code,
            price=daily_prices[date_str],
            currency=currency,
            price_date=date_str,
            source=source,
        )
        inserted += 1

    return {
        "code": code,
        "currency": currency,
        "inserted": inserted,
        "date_from": sorted_dates[0],
        "date_to": sorted_dates[-1],
        "latest_price": daily_prices[sorted_dates[-1]],
    }
