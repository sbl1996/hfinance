"""Dashboard API"""

from fastapi import APIRouter, Request

from app.models.schemas import (
    DashboardDistribution,
    DashboardOverview,
    DistributionItem,
)
from app.repositories import cash_repo, holding_repo, liability_repo, price_repo
from app.services.currency_service import convert_amount_to_cny, get_latest_cny_rate_map
from app.services.daily_metrics_service import calculate_daily_metrics

router = APIRouter()


@router.get("/overview", response_model=DashboardOverview)
async def get_overview(request: Request):
    """返回净资产、总资产、总负债、今日总盈亏、累计总盈亏"""
    cash_ratio = getattr(request.state, "cash_ratio", 1.0)
    liab_ratio = getattr(request.state, "liability_ratio", 1.0)

    total_cash_real = await cash_repo.get_total_balance()
    total_liabilities_real = await liability_repo.get_total_amount()

    total_cash = total_cash_real * cash_ratio
    total_liabilities = total_liabilities_real * liab_ratio

    # 计算投资市值
    holdings = await holding_repo.get_all()
    total_investment_mv = 0.0
    total_cost = 0.0
    ignored_market_value = 0.0
    latest_rate_map = await get_latest_cny_rate_map()

    for h in holdings:
        price_data = await price_repo.get_latest_price(h["code"])
        if price_data:
            holding_market_value = convert_amount_to_cny(
                price_data["price"] * h["quantity"],
                price_data["currency"],
                latest_rate_map,
            )
            total_investment_mv += holding_market_value
            if h["ignored"]:
                ignored_market_value += holding_market_value
        if not h["ignored"]:
            total_cost += h["cost_total_cny"]

    total_assets = total_cash + total_investment_mv
    net_assets = total_assets - total_liabilities
    total_pnl = (total_investment_mv - ignored_market_value) - total_cost

    live_metrics = await calculate_daily_metrics(is_trading_day=True)
    daily_pnl = live_metrics["total_daily_pnl"] if live_metrics else 0.0

    return DashboardOverview(
        net_assets_cny=round(net_assets, 2),
        total_assets_cny=round(total_assets, 2),
        total_liabilities_cny=round(total_liabilities, 2),
        daily_pnl_cny=round(daily_pnl, 2),
        total_pnl_cny=round(total_pnl, 2),
    )


@router.get("/distribution", response_model=DashboardDistribution)
async def get_distribution(request: Request):
    """返回现金/投资/负债占比数据"""
    cash_ratio = getattr(request.state, "cash_ratio", 1.0)
    liab_ratio = getattr(request.state, "liability_ratio", 1.0)

    total_cash_real = await cash_repo.get_total_balance()
    total_liabilities_real = await liability_repo.get_total_amount()

    total_cash = total_cash_real * cash_ratio
    total_liabilities = total_liabilities_real * liab_ratio

    holdings = await holding_repo.get_all()
    total_investment_mv = 0.0
    latest_rate_map = await get_latest_cny_rate_map()

    for h in holdings:
        price_data = await price_repo.get_latest_price(h["code"])
        if price_data:
            total_investment_mv += convert_amount_to_cny(
                price_data["price"] * h["quantity"],
                price_data["currency"],
                latest_rate_map,
            )

    # 总资产 = 现金 + 投资，用于计算占比
    total = total_cash + total_investment_mv + total_liabilities
    if total == 0:
        total = 1  # 避免除零

    items = [
        DistributionItem(
            name="现金",
            value_cny=round(total_cash, 2),
            percent=round(total_cash / total * 100, 2),
        ),
        DistributionItem(
            name="投资",
            value_cny=round(total_investment_mv, 2),
            percent=round(total_investment_mv / total * 100, 2),
        ),
        DistributionItem(
            name="负债",
            value_cny=round(total_liabilities, 2),
            percent=round(total_liabilities / total * 100, 2),
        ),
    ]
    return DashboardDistribution(items=items)
