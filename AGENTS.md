# AGENTS.md

This file provides guidance to code agents when working with code in this repository.

## Project

HFinance is a personal asset management & accounting system (个人资产管理记账系统). It tracks investments (A-stocks, HK stocks, funds), cash accounts, liabilities, and market data with portfolio analytics.

**Stack:** Vue 3 + Vite (frontend) | FastAPI + SQLite (backend) | pnpm + uv

## Commands

```bash
# Start both backend + frontend for local development
bash dev.sh

# Or start individually:
cd backend && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
cd frontend && pnpm dev          # http://localhost:5173, proxies /api -> localhost:8000

# Frontend-only:
cd frontend && pnpm build        # Production build
cd frontend && pnpm type-check   # TypeScript type checking

# Deploy to the production server
git push
sleep 3
ssh ark-1 "zsh -lic 'cd ~/Code/hfinance && git restore . && proxy_on && git pull && proxy_off && sleep 1 && bash deploy/deploy.sh'" # if the proxy fails, run `git pull` directly
```

## Architecture

**Frontend** (`frontend/`) — Mobile-first SPA with Vant UI component library:

- `src/views/` — Page-level route components (Dashboard, Investment, Accounting, Auth, Admin)
- `src/components/` — Reusable Vue SFCs (HoldingList, Watchlist, CashAccountList, forms, charts)
- `src/stores/` — Pinia stores per domain (`auth`, `holding`, `watchlist`, `dashboard`, `cash`, `liability`, `fetchTask`)
- `src/router/index.ts` — Route definitions with `requiresAuth` and `adminOnly` meta guards
- `src/utils/request.ts` — Centralized Axios instance with JWT injection, 401 redirect, error throttling
- `src/utils/format.ts` — Money formatting and color utilities (red=positive, green=negative per Chinese convention)

**Backend** (`backend/`) — Async FastAPI with layered architecture:

- `app/api/` — Route handlers (auth, cash, liabilities, holdings, watchlist, dashboard, market, fetch_tasks)
- `app/repositories/` — Data access layer (async SQLite via aiosqlite, raw SQL)
- `app/services/` — Business logic (market data via akshare, price aggregation, FX conversion, scheduler)
- `app/core/auth.py` — JWT middleware extracting user from Authorization header
- `app/core/config.py` — Pydantic Settings, all env vars prefixed `HFINANCE_`

**Auth model:** Dual-password system — admin password (full access) and guest password (scaled data via random multiplier). Guest cannot access admin-only routes or fetch tasks.

**Key config** (`frontend/vite.config.ts`):

- Vant components auto-imported on demand (no manual imports needed)
- Vue/Router/Pinia APIs auto-imported (`ref`, `computed`, `watch`, etc.) — no import statements required
- Path alias `@/` resolves to `src/`

**Database** (`backend/app/db/schema.sql`): SQLite with 9 tables — cash_accounts, liabilities, holdings, holding_sort_orders, price_cache, watchlist_items, exchange_rates, fetch_tasks, fetch_task_runs.


## Conventions

- Use short English commit messages, preferably following Conventional Commits
- Use `uv pip` for Python dependency management and `pnpm` for Node.js
- Mobile-first design (max-width 480px content area, Vant tab/nav bars)
- Before deploying to the production server, remind the user when version metadata or `docs/RELEASE_NOTES.md` may need to be updated