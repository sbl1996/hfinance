# 个人资产管理记账系统 - 开发计划

---

## 阶段 1: 项目初始化与工程脚手架 ✅

- [x] 1.1 初始化项目根目录结构：`backend/`、`frontend/`、`deploy/`
- [x] 1.2 后端：使用 uv 创建 Python 虚拟环境，添加 `pyproject.toml`，声明依赖（fastapi, uvicorn, aiosqlite, apscheduler, akshare, httpx）
- [x] 1.3 后端：创建 FastAPI 应用入口 `backend/app/main.py`，配置 CORS、路由挂载、异常处理中间件
- [x] 1.4 后端：创建配置模块 `backend/app/core/config.py`，集中管理环境变量（DB路径、定时任务时间、访问密码等）
- [x] 1.5 前端：使用 pnpm + Vite 初始化 Vue3 + TypeScript 项目 `frontend/`，安装 Vant 4、Vue Router、Axios、Pinia
- [x] 1.6 前端：配置 `vite.config.ts`（API 代理、构建输出目录），集成 `unplugin-vue-components` + `unplugin-auto-import`，实现 Vant 4 组件全自动按需引入（无需手动 import）
- [x] 1.7 前端：配置 `manifest.json` 实现 PWA 支持，设置 `meta viewport` 锁定缩放
- [x] 1.8 前端：创建 Axios 实例封装（统一 baseURL、Token 拦截器、错误处理）

---

## 阶段 2: 数据库设计与后端数据层 ✅

- [x] 2.1 设计 SQLite 数据库表结构：
  - `cash_accounts` — 现金账户（id, name, balance_cny, type[CASH/FUND], created_at, updated_at）
  - `liabilities` — 负债（id, name, amount_cny, type[CREDIT_CARD/MORTGAGE/OTHER], created_at, updated_at）
  - `holdings` — 投资持仓（id, code, name, market[A_STOCK/HK_STOCK/FUND], quantity, cost_total_cny, created_at, updated_at）
  - `price_cache` — 行情缓存（id, code, price, currency[CNY/HKD], price_date, source）
  - `exchange_rates` — 汇率缓存（id, pair[HKDCNY], rate, rate_date, source）
  - `daily_snapshots` — 每日快照（id, snapshot_date, total_assets_cny, total_liabilities_cny, net_assets_cny, daily_pnl_cny）
  - `daily_holding_snapshots` — 持仓日快照（id, snapshot_id, holding_id, code, name, quantity, price, currency, market_value_cny, daily_pnl_cny）
- [x] 2.2 创建 `backend/app/db/` 模块：`connection.py`（SQLite 连接管理）、`schema.sql`（建表语句）、`init_db.py`（初始化脚本）
- [x] 2.3 创建 `backend/app/models/` 模块：为每张表定义 Pydantic Model（请求/响应 Schema）
- [x] 2.4 创建 `backend/app/repositories/` 模块：为每张表实现 CRUD Repository（参数化查询，防 SQL 注入）

---

## 阶段 3: 后端核心 API 开发 ✅

- [x] 3.1 认证模块 `backend/app/api/auth.py`：
  - `POST /api/auth/login` — 验证访问密码，返回 JWT Token
  - `POST /api/auth/verify` — 验证 Token 有效性
- [x] 3.2 现金账户 API `backend/app/api/cash.py`：
  - `GET /api/cash` — 获取所有现金账户列表及总额
  - `POST /api/cash` — 新增现金账户
  - `PUT /api/cash/{id}` — 修改现金账户
  - `DELETE /api/cash/{id}` — 删除现金账户
- [x] 3.3 负债 API `backend/app/api/liabilities.py`：
  - `GET /api/liabilities` — 获取所有负债列表及总额
  - `POST /api/liabilities` — 新增负债
  - `PUT /api/liabilities/{id}` — 修改负债
  - `DELETE /api/liabilities/{id}` — 删除负债
- [x] 3.4 持仓 API `backend/app/api/holdings.py`：
  - `GET /api/holdings` — 获取所有持仓列表（含最新价、市值CNY、收益率计算）
  - `POST /api/holdings` — 新增持仓
  - `PUT /api/holdings/{id}` — 修改持仓
  - `DELETE /api/holdings/{id}` — 删除持仓
- [x] 3.5 Dashboard API `backend/app/api/dashboard.py`：
  - `GET /api/dashboard/overview` — 返回净资产、总资产、总负债、今日总盈亏、累计总盈亏
  - `GET /api/dashboard/distribution` — 返回现金/投资/负债占比数据
  - `GET /api/dashboard/calendar?year=2025&month=6` — 返回指定月份每日盈亏数据
  - `GET /api/dashboard/calendar/{date}` — 返回指定日期各标的盈亏明细

---

## 阶段 4: 行情抓取引擎与快照系统 ✅

- [x] 4.1 创建 `backend/app/services/market_fetcher.py`：
  - 实现 `fetch_hk_stock(code)` — 调用 AKShare `stock_hk_spot_em` 获取港股价格
  - 实现 `fetch_a_etf(code)` — 调用 AKShare `fund_etf_spot_em` / `stock_zh_a_spot_em` 获取 A 股/ETF 价格
  - 实现 `fetch_fund_nav(code)` — 调用 AKShare `fund_open_fund_info_em` 获取基金净值
  - 实现 `fetch_hkdcny_rate()` — 调用 AKShare `fx_spot_quote` 获取 HKD/CNY 汇率
- [x] 4.2 创建 `backend/app/services/price_service.py`：
  - 实现 `update_all_prices()` — 遍历所有持仓，调用对应 fetcher，写入 `price_cache` 和 `exchange_rates`
  - 实现抓取失败降级逻辑：超时/报错时沿用上一交易日价格，标记 `is_stale=True`
- [x] 4.3 创建 `backend/app/services/snapshot_service.py`：
  - 实现 `generate_daily_snapshot()` — 计算今日盈亏（剥离现金流），写入 `daily_snapshots` 和 `daily_holding_snapshots`
  - 盈亏公式：(今日最新价 - 昨日收盘价) x 今日持仓数量 x 汇率
  - ⚠️ **已知 Limitation**：当用户在当日进行加仓/减仓操作时，由于使用「今日持仓数量」参与计算，会导致当日盈亏快照出现轻微偏差（如昨日持有100股，今日加仓至200股，则价差盈亏会被放大）。极简系统不引入流水账表，接受此小概率误差。**代码注释中须明确标出此 Limitation，前端盈亏日历弹窗中需提示：「当日调仓可能会导致当日盈亏快照出现轻微偏差」**
- [x] 4.4 创建 `backend/app/services/scheduler.py`：
  - 配置 APScheduler，设定**每天** 16:30 自动执行 `update_all_prices()` + `generate_daily_snapshot()`（不判断交易日，每天无脑执行）
  - 非交易日自动跳过逻辑：在 `update_all_prices()` 后判断，若 AKShare 抓取回来的 `price_date` 与上一日相同（说明今日未开盘），则当日 `daily_pnl_cny` 直接记为 `0`，不重复计算。这样无需维护节假日日历，完美兼容所有休市情况
- [x] 4.5 行情刷新 API `backend/app/api/market.py`：
  - `POST /api/market/refresh` — 手动触发全量行情更新 + 快照生成

---

## 阶段 5: 前端页面与组件开发 ✅

- [x] 5.1 全局布局与导航：
  - 创建 `App.vue` 底部 Tab 导航栏（总览 / 投资 / 记账）三个 Tab
  - 配置 Vue Router 路由（`/dashboard`、`/investment`、`/accounting`）
  - 创建 `AuthView.vue` 密码输入页面（首次进入或 Token 过期时展示）
- [x] 5.2 总览页面 `DashboardView.vue`：
  - 资产总览卡片组件 `OverviewCard.vue`（净资产、总资产、总负债、今日盈亏、累计盈亏）
  - 资产分布环形图组件 `DistributionChart.vue`（使用 CSS `conic-gradient` 手搓实现，保持极小 Bundle Size）
  - 盈亏日历组件 `PnlCalendar.vue`（月历网格，红涨绿跌，点击弹出明细弹窗）
- [x] 5.3 投资页面 `InvestmentView.vue`：
  - 持仓明细列表组件 `HoldingList.vue`（名称、代码、数量、最新价、市值CNY、收益率）
  - 持仓新增/编辑弹窗组件 `HoldingForm.vue`（市场选择、代码输入、数量、成本总额CNY）
  - 强制刷新按钮（调用 `/api/market/refresh`，展示加载状态）
  - 数据陈旧提示标识（价格缓存非当日时显示"数据陈旧"标签）
- [x] 5.4 记账页面 `AccountingView.vue`：
  - 现金账户列表组件 `CashAccountList.vue`（支持增删改）
  - 现金账户编辑弹窗组件 `CashAccountForm.vue`
  - 负债列表组件 `LiabilityList.vue`（支持增删改）
  - 负债编辑弹窗组件 `LiabilityForm.vue`
- [x] 5.5 通用组件与工具：
  - 数字输入组件（通过 inputmode="decimal" 实现原生数字键盘）
  - 金额格式化工具函数 `formatMoney(value, currency)`
  - Pinia Store：`useAuthStore`、`useDashboardStore`、`useHoldingStore`、`useCashStore`、`useLiabilityStore`

---

## 阶段 6: 前后端联调与业务逻辑验证 ✅

- [x] 6.1 验证认证流程：密码登录 -> Token 存储 -> 请求拦截 -> Token 过期重新登录
- [x] 6.2 验证现金/负债 CRUD 全流程：新增 -> 列表展示 -> 编辑 -> 删除
- [x] 6.3 验证持仓 CRUD 全流程：新增 -> 列表展示（含最新价/市值/收益率计算） -> 编辑 -> 删除
- [x] 6.4 验证 Dashboard 数据正确性：净资产 = 总资产 - 总负债，盈亏计算公式正确
- [x] 6.5 验证盈亏日历：日历网格渲染、颜色标识（红涨绿跌）、点击弹出明细
- [x] 6.6 验证行情抓取：手动触发刷新 -> 价格更新 -> 市值重算 -> 快照生成
- [x] 6.7 验证降级策略：模拟 AKShare 接口失败，确认沿用旧价格并显示"数据陈旧"提示
- [x] 6.8 移动端适配验证：底部导航交互、大尺寸热区(>=44px)、禁止横向滚动、数字键盘

---

## 阶段 7: 部署配置与运维脚本 ✅

- [x] 7.1 编写 Nginx 配置文件 `deploy/nginx/hfinance.conf`（反向代理 + SSL + 前端静态文件）
- [x] 7.2 编写 Systemd 服务文件 `deploy/systemd/hfinance.service`（Uvicorn 守护进程）
- [x] 7.3 编写一键部署脚本 `deploy/deploy.sh`（前端构建 -> 后端安装 -> Nginx 配置 -> Systemd 启动）
- [x] 7.4 编写数据库备份脚本 `deploy/backup.sh`（SQLite 文件定时拷贝）

---

## 阶段 8: 收尾与优化 ✅

- [x] 8.1 首次运行引导体验：检测数据库是否初始化，未初始化时引导设置访问密码
- [x] 8.2 前端加载优化：路由懒加载、Vant 组件按需引入
- [x] 8.3 错误边界与友好提示：网络错误、接口异常的全局 Toast 处理
- [x] 8.4 代码清理：移除调试日志、统一代码风格、添加必要注释
