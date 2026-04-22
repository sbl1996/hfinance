-- HFinance 数据库建表语句
-- SQLite3

-- 现金账户表
CREATE TABLE IF NOT EXISTS cash_accounts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    balance_cny REAL    NOT NULL DEFAULT 0,
    type        TEXT    NOT NULL DEFAULT 'CASH' CHECK(type IN ('CASH', 'FUND')),
    created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- 负债表
CREATE TABLE IF NOT EXISTS liabilities (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    amount_cny  REAL    NOT NULL DEFAULT 0,
    type        TEXT    NOT NULL DEFAULT 'OTHER' CHECK(type IN ('CREDIT_CARD', 'MORTGAGE', 'OTHER')),
    created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- 投资持仓表
CREATE TABLE IF NOT EXISTS holdings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT    NOT NULL,
    name            TEXT    NOT NULL,
    market          TEXT    NOT NULL DEFAULT 'A_STOCK' CHECK(market IN ('A_STOCK', 'HK_STOCK', 'FUND')),
    quantity        REAL    NOT NULL DEFAULT 0,
    cost_total_cny  REAL    NOT NULL DEFAULT 0,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- 持仓排序表
CREATE TABLE IF NOT EXISTS holding_sort_orders (
    holding_id   INTEGER PRIMARY KEY,
    sort_order   INTEGER NOT NULL,
    ignored      INTEGER NOT NULL DEFAULT 0,
    updated_at   TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (holding_id) REFERENCES holdings(id) ON DELETE CASCADE
);

-- 行情缓存表
CREATE TABLE IF NOT EXISTS price_cache (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    code         TEXT    NOT NULL,
    price        REAL    NOT NULL,
    currency     TEXT    NOT NULL DEFAULT 'CNY' CHECK(currency IN ('CNY', 'HKD')),
    price_date   TEXT    NOT NULL,
    source       TEXT    NOT NULL DEFAULT 'akshare',
    created_at   TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    UNIQUE(code, price_date)
);

-- 汇率缓存表
CREATE TABLE IF NOT EXISTS exchange_rates (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    pair        TEXT    NOT NULL DEFAULT 'HKDCNY',
    rate        REAL    NOT NULL,
    rate_date   TEXT    NOT NULL,
    source      TEXT    NOT NULL DEFAULT 'akshare',
    created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    UNIQUE(pair, rate_date)
);

-- 每日快照表
CREATE TABLE IF NOT EXISTS daily_snapshots (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date       TEXT    NOT NULL UNIQUE,
    total_assets_cny    REAL    NOT NULL DEFAULT 0,
    total_liabilities_cny REAL  NOT NULL DEFAULT 0,
    net_assets_cny      REAL    NOT NULL DEFAULT 0,
    daily_pnl_cny       REAL    NOT NULL DEFAULT 0,
    created_at          TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_price_cache_code ON price_cache(code);
CREATE INDEX IF NOT EXISTS idx_price_cache_date ON price_cache(price_date);
CREATE INDEX IF NOT EXISTS idx_holding_sort_orders_sort_order ON holding_sort_orders(sort_order);
CREATE INDEX IF NOT EXISTS idx_exchange_rates_pair ON exchange_rates(pair);
CREATE INDEX IF NOT EXISTS idx_exchange_rates_date ON exchange_rates(rate_date);
CREATE INDEX IF NOT EXISTS idx_daily_snapshots_date ON daily_snapshots(snapshot_date);
