"""历史价格全量导入服务"""

import akshare as ak

from app.models.schemas import IndexImportPrefixType
from app.repositories import price_repo
from app.services.network_proxy_state import outbound_proxy_env


def fetch_fund_history(code: str):
    with outbound_proxy_env():
        df = ak.fund_open_fund_info_em(symbol=code)
    if df.empty:
        raise ValueError(f"基金 {code} 未获取到净值数据")
    return df


def fetch_us_stock_history(code: str):
    with outbound_proxy_env():
        df = ak.index_us_stock_sina(symbol=code)
    if df.empty:
        raise ValueError(f"美股 {code} 未获取到历史行情")
    return df


def build_cn_index_symbol(code: str, prefix_type: IndexImportPrefixType) -> str:
    normalized_code = str(code).strip()
    if not normalized_code:
        raise ValueError("指数代码不能为空")

    return f"{prefix_type.value.lower()}{normalized_code.lower()}"


def fetch_cn_index_history(code: str, prefix_type: IndexImportPrefixType):
    symbol = build_cn_index_symbol(code, prefix_type)
    with outbound_proxy_env():
        df = ak.stock_zh_index_daily_em(
            symbol=symbol,
            start_date="20200101",
            end_date="20500101",
        )
    if df.empty:
        raise ValueError(f"指数 {code} 未获取到历史行情")
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


def load_daily_closes_from_dataframe(df) -> dict[str, float]:
    daily_prices: dict[str, float] = {}
    required_columns = {"date", "close"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(f"历史数据缺少必要列: {', '.join(sorted(missing_columns))}")

    for row_no, (_, row) in enumerate(df.iterrows(), start=2):
        date_value = row.get("date")
        close_value = row.get("close")
        date_str = str(date_value or "").strip()[:10]
        if not date_str or close_value is None:
            continue

        try:
            daily_prices[date_str] = float(close_value)
        except ValueError as exc:
            raise ValueError(f"第 {row_no} 行 close 无法解析: {close_value}") from exc

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


async def import_us_stock_history(code: str, currency: str = "USD", source: str = "ak_share") -> dict:
    df = fetch_us_stock_history(code)
    daily_prices = load_daily_closes_from_dataframe(df)
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


async def import_cn_index_history(
    code: str,
    prefix_type: IndexImportPrefixType,
    currency: str = "CNY",
    source: str = "ak_share",
) -> dict:
    df = fetch_cn_index_history(code, prefix_type)
    daily_prices = load_daily_closes_from_dataframe(df)
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
