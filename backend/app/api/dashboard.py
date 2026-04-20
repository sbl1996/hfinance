"""Dashboard API"""

from fastapi import APIRouter

from app.models.schemas import (
    DashboardOverview, DashboardDistribution, DistributionItem,
    CalendarMonthOut, CalendarDayPnl, DailyHoldingSnapshotOut,
)
from app.repositories import cash_repo, liability_repo, holding_repo, price_repo, snapshot_repo

router = APIRouter()


@router.get("/overview", response_model=DashboardOverview)
async def get_overview():
    """返回净资产、总资产、总负债、今日总盈亏、累计总盈亏"""
    total_cash = await cash_repo.get_total_balance()
    total_liabilities = await liability_repo.get_total_amount()

    # 计算投资市值
    holdings = await holding_repo.get_all()
    total_investment_mv = 0.0
    total_cost = 0.0
    rate_data = await price_repo.get_latest_rate("HKDCNY")
    hkdcny_rate = rate_data["rate"] if rate_data else 1.0

    for h in holdings:
        price_data = await price_repo.get_latest_price(h["code"])
        if price_data:
            if h["market"] == "HK_STOCK":
                total_investment_mv += price_data["price"] * h["quantity"] * hkdcny_rate
            else:
                total_investment_mv += price_data["price"] * h["quantity"]
        total_cost += h["cost_total_cny"]

    total_assets = total_cash + total_investment_mv
    net_assets = total_assets - total_liabilities
    total_pnl = total_investment_mv - total_cost

    # 今日盈亏取最新快照
    latest_snapshot = await snapshot_repo.get_latest_snapshot()
    daily_pnl = latest_snapshot["daily_pnl_cny"] if latest_snapshot else 0.0

    return DashboardOverview(
        net_assets_cny=round(net_assets, 2),
        total_assets_cny=round(total_assets, 2),
        total_liabilities_cny=round(total_liabilities, 2),
        daily_pnl_cny=round(daily_pnl, 2),
        total_pnl_cny=round(total_pnl, 2),
    )


@router.get("/distribution", response_model=DashboardDistribution)
async def get_distribution():
    """返回现金/投资/负债占比数据"""
    total_cash = await cash_repo.get_total_balance()
    total_liabilities = await liability_repo.get_total_amount()

    holdings = await holding_repo.get_all()
    total_investment_mv = 0.0
    rate_data = await price_repo.get_latest_rate("HKDCNY")
    hkdcny_rate = rate_data["rate"] if rate_data else 1.0

    for h in holdings:
        price_data = await price_repo.get_latest_price(h["code"])
        if price_data:
            if h["market"] == "HK_STOCK":
                total_investment_mv += price_data["price"] * h["quantity"] * hkdcny_rate
            else:
                total_investment_mv += price_data["price"] * h["quantity"]

    # 总资产 = 现金 + 投资，用于计算占比
    total = total_cash + total_investment_mv + total_liabilities
    if total == 0:
        total = 1  # 避免除零

    items = [
        DistributionItem(name="现金", value_cny=round(total_cash, 2), percent=round(total_cash / total * 100, 2)),
        DistributionItem(name="投资", value_cny=round(total_investment_mv, 2), percent=round(total_investment_mv / total * 100, 2)),
        DistributionItem(name="负债", value_cny=round(total_liabilities, 2), percent=round(total_liabilities / total * 100, 2)),
    ]
    return DashboardDistribution(items=items)


@router.get("/calendar", response_model=CalendarMonthOut)
async def get_calendar(year: int, month: int):
    """返回指定月份每日盈亏数据"""
    rows = await snapshot_repo.get_month_pnl(year, month)
    days = [CalendarDayPnl(date=r["snapshot_date"], daily_pnl_cny=r["daily_pnl_cny"]) for r in rows]
    return CalendarMonthOut(year=year, month=month, days=days)


@router.get("/calendar/{date}")
async def get_calendar_detail(date: str):
    """返回指定日期各标的盈亏明细"""
    snapshots = await snapshot_repo.get_holding_snapshots_by_date(date)
    return [DailyHoldingSnapshotOut(**s) for s in snapshots]
