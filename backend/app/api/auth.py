"""认证 API"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from jose import JWTError, jwt

from app.core.config import get_settings
from app.models.schemas import LoginRequest, TokenResponse

router = APIRouter()
settings = get_settings()


def _create_token() -> str:
    """生成 JWT Token"""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"exp": expire, "sub": "hfinance_user"}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str) -> bool:
    """验证 JWT Token 是否有效"""
    try:
        jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return True
    except JWTError:
        return False


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """验证访问密码，返回 JWT Token"""
    if req.password != settings.ACCESS_PASSWORD:
        raise HTTPException(status_code=401, detail="密码错误")
    token = _create_token()
    return TokenResponse(token=token)


@router.post("/verify")
async def verify(token_data: dict):
    """验证 Token 有效性"""
    token = token_data.get("token", "")
    if verify_token(token):
        return {"valid": True}
    raise HTTPException(status_code=401, detail="Token 无效或已过期")
