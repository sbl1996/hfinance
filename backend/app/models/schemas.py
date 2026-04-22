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


class CurrencyType(str, Enum):
    CNY = "CNY"
    HKD = "HKD"


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


# ============ 每日快照 ============

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


# ============ 认证 ============

class LoginRequest(BaseModel):
    password: str


class TokenResponse(BaseModel):
    token: str
