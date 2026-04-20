"""认证中间件 - 保护 API 路由"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.api.auth import verify_token

# 不需要认证的路径
PUBLIC_PATHS = {"/api/auth/login", "/api/auth/verify", "/docs", "/redoc", "/openapi.json"}


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
        token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""

        if not token or not verify_token(token):
            return JSONResponse(
                status_code=401,
                content={"detail": "未授权，请先登录"},
            )

        return await call_next(request)
