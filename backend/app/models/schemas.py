"""Pydantic Model - 请求/响应 Schema"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ============ 枚举类型 ============

class CashAccountType(str, Enum):
    CASH = "CASH"
    FUND = "FUND"


class LiabilityType(str, Enum):
    CREDIT_CARD = "CREDIT_CARD"
    MORTGAGE = "MORTGAGE"
    OTHER = "OTHER"


class MarketType(str, Enum):
    A_STOCK = "A_STOCK"
    HK_STOCK = "HK_STOCK"
    FUND = "FUND"


class WatchMarketType(str, Enum):
    A_STOCK = "A_STOCK"
    HK_STOCK = "HK_STOCK"
    FUND = "FUND"
    US_STOCK = "US_STOCK"
    CN_INDEX = "CN_INDEX"


class FetchTaskMarketType(str, Enum):
    A_STOCK = "A_STOCK"
    HK_STOCK = "HK_STOCK"
    FUND = "FUND"
    US_STOCK = "US_STOCK"
    CN_INDEX = "CN_INDEX"


class CurrencyType(str, Enum):
    CNY = "CNY"
    HKD = "HKD"
    USD = "USD"


class FetchTaskRunStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


# ============ 现金账户 ============

class CashAccountCreate(BaseModel):
    name: str
    balance_cny: float = 0
    type: CashAccountType = CashAccountType.CASH


class CashAccountUpdate(BaseModel):
    name: Optional[str] = None
    balance_cny: Optional[float] = None
    type: Optional[CashAccountType] = None


class CashAccountOut(BaseModel):
    id: int
    name: str
    balance_cny: float
    type: CashAccountType
    created_at: str
    updated_at: str


class CashAccountListOut(BaseModel):
    items: list[CashAccountOut]
    total_balance_cny: float


# ============ 负债 ============

class LiabilityCreate(BaseModel):
    name: str
    amount_cny: float = 0
    type: LiabilityType = LiabilityType.OTHER


class LiabilityUpdate(BaseModel):
    name: Optional[str] = None
    amount_cny: Optional[float] = None
    type: Optional[LiabilityType] = None


class LiabilityOut(BaseModel):
    id: int
    name: str
    amount_cny: float
    type: LiabilityType
    created_at: str
    updated_at: str


class LiabilityListOut(BaseModel):
    items: list[LiabilityOut]
    total_amount_cny: float


# ============ 持仓 ============

class HoldingCreate(BaseModel):
    code: str
    name: str
    market: MarketType = MarketType.A_STOCK
    quantity: float = 0
    cost_total_cny: float = 0


class HoldingUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    market: Optional[MarketType] = None
    quantity: Optional[float] = None
    cost_total_cny: Optional[float] = None


class HoldingIgnoreUpdate(BaseModel):
    ignored: bool


class HoldingOut(BaseModel):
    id: int
    code: str
    name: str
    market: MarketType
    quantity: float
    cost_total_cny: float
    sort_order: int = 0
    ignored: bool = False
    # 以下字段由 API 层动态计算
    latest_price: Optional[float] = None
    price_currency: Optional[CurrencyType] = None
    price_date: Optional[str] = None
    growth_rate: Optional[float] = None
    growth_pnl_cny: Optional[float] = None
    market_value_cny: Optional[float] = None
    pnl_cny: Optional[float] = None
    pnl_rate: Optional[float] = None
    hkdcny_rate: Optional[float] = None
    created_at: str
    updated_at: str


class HoldingListOut(BaseModel):
    items: list[HoldingOut]
    total_market_value_cny: float
    total_cost_cny: float
    total_pnl_cny: float
    daily_pnl_cny: float = 0.0


class HoldingReorderItem(BaseModel):
    id: int
    sort_order: int = Field(ge=0)


class HoldingReorderRequest(BaseModel):
    items: list[HoldingReorderItem]


# ============ 自选标的 ============

class WatchlistItemCreate(BaseModel):
    code: str
    name: str
    market: WatchMarketType


class WatchlistItemUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    market: Optional[WatchMarketType] = None


class WatchlistItemOut(BaseModel):
    id: int
    code: str
    name: str
    market: WatchMarketType
    latest_price: Optional[float] = None
    price_currency: Optional[CurrencyType] = None
    price_date: Optional[str] = None
    growth_rate: Optional[float] = None
    created_at: str
    updated_at: str


class WatchlistItemListOut(BaseModel):
    items: list[WatchlistItemOut]


# ============ 行情缓存 ============

class PriceCacheOut(BaseModel):
    code: str
    price: float
    currency: CurrencyType
    price_date: str
    source: str


# ============ 汇率缓存 ============

class ExchangeRateOut(BaseModel):
    pair: str
    rate: float
    rate_date: str
    source: str


# ============ 持仓走势 ============

class PriceHistoryItem(BaseModel):
    date: str
    price: float
    yield_rate: Optional[float] = None


class PriceHistoryResponse(BaseModel):
    code: str
    name: str
    unit_cost: float
    market: MarketType
    current_price: Optional[float] = None
    price_currency: Optional[CurrencyType] = None
    price_date: Optional[str] = None
    market_value_cny: Optional[float] = None
    pnl_cny: Optional[float] = None
    pnl_rate: Optional[float] = None
    growth_rate: Optional[float] = None
    growth_pnl_cny: Optional[float] = None
    quantity: float
    cost_total_cny: float
    history: list[PriceHistoryItem]
    empty: bool


class WatchlistPriceHistoryResponse(BaseModel):
    id: int
    code: str
    name: str
    market: WatchMarketType
    latest_price: Optional[float] = None
    current_price: Optional[float] = None
    price_currency: Optional[CurrencyType] = None
    price_date: Optional[str] = None
    growth_rate: Optional[float] = None
    created_at: str
    updated_at: str
    history: list[PriceHistoryItem]
    empty: bool


# ============ Dashboard ============

class DashboardOverview(BaseModel):
    net_assets_cny: float
    total_assets_cny: float
    total_liabilities_cny: float
    daily_pnl_cny: float
    total_pnl_cny: float


class DistributionItem(BaseModel):
    name: str
    value_cny: float
    percent: float


class DashboardDistribution(BaseModel):
    items: list[DistributionItem]


# ============ 自动拉取任务 ============

class FetchTaskBase(BaseModel):
    code: str
    name: str
    market: FetchTaskMarketType
    enabled: bool = True
    run_time: str = Field(pattern=r"^\d{2}:\d{2}$")
    weekdays: list[int] = Field(min_length=1)


class FetchTaskCreate(FetchTaskBase):
    pass


class FetchTaskUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    market: Optional[FetchTaskMarketType] = None
    enabled: Optional[bool] = None
    run_time: Optional[str] = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    weekdays: Optional[list[int]] = None


class FetchTaskToggleRequest(BaseModel):
    enabled: bool


class FetchTaskRunSummary(BaseModel):
    id: int
    scheduled_for: str
    status: FetchTaskRunStatus
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    error_message: Optional[str] = None
    price_date: Optional[str] = None
    price_value: Optional[float] = None


class FetchTaskOut(BaseModel):
    id: int
    code: str
    name: str
    market: FetchTaskMarketType
    enabled: bool
    run_time: str
    weekdays: list[int]
    created_at: str
    updated_at: str
    latest_run: Optional[FetchTaskRunSummary] = None


class FetchTaskListOut(BaseModel):
    items: list[FetchTaskOut]


class FetchTaskRunsOut(BaseModel):
    items: list[FetchTaskRunSummary]


# ============ 认证 ============

class LoginRequest(BaseModel):
    password: str


class TokenResponse(BaseModel):
    token: str
