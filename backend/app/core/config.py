"""全局配置模块 - 集中管理环境变量与应用配置"""

import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置，优先从环境变量读取，未设置则使用默认值"""

    # ---- 数据库 ----
    DB_PATH: str = str(Path(__file__).resolve().parent.parent.parent / "data" / "hfinance.db")

    # ---- 认证 ----
    ACCESS_PASSWORD: str = "hfinance"  # 访问密码，生产环境务必修改
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # Token 有效期 7 天

    # ---- 定时任务 ----
    SCHEDULER_HOUR: int = 16
    SCHEDULER_MINUTE: int = 30

    # ---- 行情抓取 ----
    MARKET_FETCH_TIMEOUT: int = 30  # 单次抓取超时秒数

    # ---- 服务 ----
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    model_config = {"env_prefix": "HFINANCE_", "env_file": ".env", "extra": "ignore"}


def get_settings() -> Settings:
    """获取全局配置单例"""
    return Settings()


# 确保 DB 所在目录存在
_db_dir = os.path.dirname(get_settings().DB_PATH)
os.makedirs(_db_dir, exist_ok=True)
