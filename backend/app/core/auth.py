"""认证中间件 - 保护 API 路由"""

import hashlib
from datetime import datetime

from fastapi import Request
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.api.auth import verify_token
from app.core.config import get_settings

# 不需要认证的路径
PUBLIC_PATHS = {
    "/api/auth/login",
    "/api/auth/verify",
    "/docs",
    "/redoc",
    "/openapi.json",
}
settings = get_settings()


def get_weekly_ratios() -> tuple[float, float]:
    """基于当前年份和周数生成独立的现金和负债随机系数"""
    year, week, _ = datetime.now().isocalendar()

    # 现金系数
    seed_cash = f"hfinance-guest-cash-{year}-W{week}-{settings.JWT_SECRET_KEY}"
    hash_int_cash = int(hashlib.md5(seed_cash.encode()).hexdigest()[:8], 16)
    fraction_cash = hash_int_cash / 0xFFFFFFFF

    # 负债系数
    seed_liab = f"hfinance-guest-liab-{year}-W{week}-{settings.JWT_SECRET_KEY}"
    hash_int_liab = int(hashlib.md5(seed_liab.encode()).hexdigest()[:8], 16)
    fraction_liab = hash_int_liab / 0xFFFFFFFF

    ratio_range = settings.GUEST_RATIO_MAX - settings.GUEST_RATIO_MIN
    cash_ratio = round(settings.GUEST_RATIO_MIN + (fraction_cash * ratio_range), 4)
    liab_ratio = round(settings.GUEST_RATIO_MIN + (fraction_liab * ratio_range), 4)

    return cash_ratio, liab_ratio


class AuthMiddleware(BaseHTTPMiddleware):
    """全局认证中间件：除了公开路径外，所有请求需要携带有效 Token"""

    async def dispatch(self, request: Request, call_next):
        # 非 API 路径直接放行
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        # 公开路径放行
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        # 验证 Token
        auth_header = request.headers.get("Authorization", "")
        token = (
            auth_header.replace("Bearer ", "")
            if auth_header.startswith("Bearer ")
            else ""
        )

        if not token or not verify_token(token):
            return JSONResponse(
                status_code=401,
                content={"detail": "未授权，请先登录"},
            )

        # 解析角色并挂载访客系数
        role = "admin"
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )
            role = payload.get("sub", "admin")
        except JWTError:
            pass

        if role == "guest":
            cash_ratio, liab_ratio = get_weekly_ratios()
            request.state.cash_ratio = cash_ratio
            request.state.liability_ratio = liab_ratio
            # 访客模式禁止写操作
            if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "隐私访客模式下仅允许查看数据"},
                )
        else:
            request.state.cash_ratio = 1.0
            request.state.liability_ratio = 1.0

        return await call_next(request)
