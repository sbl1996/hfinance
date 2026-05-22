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
    currency     TEXT    NOT NULL DEFAULT 'CNY' CHECK(currency IN ('CNY', 'HKD', 'USD')),
    price_date   TEXT    NOT NULL,
    source       TEXT    NOT NULL DEFAULT 'akshare',
    created_at   TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    UNIQUE(code, price_date)
);

-- 自选标的表
CREATE TABLE IF NOT EXISTS watchlist_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT    NOT NULL,
    name        TEXT    NOT NULL,
    market      TEXT    NOT NULL CHECK(market IN ('A_STOCK', 'HK_STOCK', 'FUND', 'US_STOCK')),
    sort_order  INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
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

-- 自动拉取任务表
CREATE TABLE IF NOT EXISTS fetch_tasks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT    NOT NULL,
    name            TEXT    NOT NULL,
    market          TEXT    NOT NULL CHECK(market IN ('A_STOCK', 'HK_STOCK', 'FUND')),
    enabled         INTEGER NOT NULL DEFAULT 1,
    run_time        TEXT    NOT NULL,
    weekdays_mask   INTEGER NOT NULL,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    UNIQUE(code, market, run_time, weekdays_mask)
);

-- 自动拉取任务执行记录表
CREATE TABLE IF NOT EXISTS fetch_task_runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id         INTEGER NOT NULL,
    code            TEXT    NOT NULL,
    name            TEXT    NOT NULL,
    market          TEXT    NOT NULL CHECK(market IN ('A_STOCK', 'HK_STOCK', 'FUND')),
    scheduled_for   TEXT    NOT NULL,
    status          TEXT    NOT NULL CHECK(status IN ('PENDING', 'RUNNING', 'SUCCESS', 'FAILED')),
    started_at      TEXT,
    finished_at     TEXT,
    error_message   TEXT,
    price_date      TEXT,
    price_value     REAL,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (task_id) REFERENCES fetch_tasks(id) ON DELETE CASCADE,
    UNIQUE(task_id, scheduled_for)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_price_cache_code ON price_cache(code);
CREATE INDEX IF NOT EXISTS idx_price_cache_date ON price_cache(price_date);
CREATE INDEX IF NOT EXISTS idx_watchlist_items_sort_order ON watchlist_items(sort_order, id);
CREATE INDEX IF NOT EXISTS idx_holding_sort_orders_sort_order ON holding_sort_orders(sort_order);
CREATE INDEX IF NOT EXISTS idx_exchange_rates_pair ON exchange_rates(pair);
CREATE INDEX IF NOT EXISTS idx_exchange_rates_date ON exchange_rates(rate_date);
CREATE INDEX IF NOT EXISTS idx_fetch_tasks_enabled_time ON fetch_tasks(enabled, run_time);
CREATE INDEX IF NOT EXISTS idx_fetch_task_runs_status_scheduled ON fetch_task_runs(status, scheduled_for, id);
CREATE INDEX IF NOT EXISTS idx_fetch_task_runs_task_scheduled ON fetch_task_runs(task_id, scheduled_for DESC, id DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_fetch_task_runs_one_active
ON fetch_task_runs(task_id)
WHERE status IN ('PENDING', 'RUNNING');
