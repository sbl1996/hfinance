"""FastAPI 应用入口"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import auth, cash, liabilities, holdings, dashboard, market
from app.core.config import get_settings
from app.core.auth import AuthMiddleware
from app.db.init_db import init_database
from app.db.connection import close_db
from app.services.scheduler import start_scheduler

settings = get_settings()

app = FastAPI(
    title="HFinance - 个人资产管理记账系统",
    version="0.1.0",
    docs_url=None,  # 生产环境关闭 Swagger UI
    redoc_url=None,
)

# ---- CORS ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 个人使用，不限制来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- 认证中间件 ----
app.add_middleware(AuthMiddleware)


# ---- 全局异常处理 ----
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"服务器内部错误: {str(exc)}"},
    )


# ---- 路由挂载 ----
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(cash.router, prefix="/api/cash", tags=["现金账户"])
app.include_router(liabilities.router, prefix="/api/liabilities", tags=["负债"])
app.include_router(holdings.router, prefix="/api/holdings", tags=["持仓"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["总览"])
app.include_router(market.router, prefix="/api/market", tags=["行情"])


# ---- 启动/关闭事件 ----
@app.on_event("startup")
async def on_startup():
    await init_database()
    start_scheduler()


@app.on_event("shutdown")
async def on_shutdown():
    await close_db()
