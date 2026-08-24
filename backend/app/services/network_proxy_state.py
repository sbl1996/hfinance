"""Per-source network route policies for outbound fetches."""

from __future__ import annotations

import os
import json
from contextlib import contextmanager
from threading import Lock, RLock
from typing import Iterator

from app.db.connection import get_db

VPN_PROXY_URL = "http://127.0.0.1:7890"
_PROXY_ENV_KEYS = ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy")
ROUTE_POLICY_KEY = "market_route_policies"
DIRECT = "DIRECT"
VPN = "VPN"
ROUTE_SOURCES = (
    "YAHOO", "XUEQIU", "EASTMONEY", "TENCENT", "FUTU",
    "AK_HK", "AK_FUND", "AK_A", "AK_US", "CHINAMONEY",
)
DEFAULT_ROUTE_POLICIES = {source: (VPN if source == "YAHOO" else DIRECT) for source in ROUTE_SOURCES}

_route_policies = dict(DEFAULT_ROUTE_POLICIES)
_state_lock = Lock()
_env_lock = RLock()


def get_route_policies() -> dict[str, str]:
    with _state_lock:
        return dict(_route_policies)


async def load_route_policies() -> None:
    db = await get_db()
    cursor = await db.execute(
        "SELECT value FROM runtime_settings WHERE key = ?", (ROUTE_POLICY_KEY,)
    )
    row = await cursor.fetchone()
    policies = dict(DEFAULT_ROUTE_POLICIES)
    if row:
        try:
            saved = json.loads(row[0])
            for source in ROUTE_SOURCES:
                if saved.get(source) in (DIRECT, VPN):
                    policies[source] = saved[source]
        except (AttributeError, TypeError, ValueError, json.JSONDecodeError):
            pass
    with _state_lock:
        _route_policies.clear()
        _route_policies.update(policies)
    await db.execute(
        "INSERT OR REPLACE INTO runtime_settings (key, value) VALUES (?, ?)",
        (ROUTE_POLICY_KEY, json.dumps(policies, ensure_ascii=False)),
    )
    await db.commit()


async def set_route_policies(policies: dict[str, str]) -> dict[str, str]:
    next_policies = dict(DEFAULT_ROUTE_POLICIES)
    for source, policy in policies.items():
        if source not in ROUTE_SOURCES:
            raise ValueError(f"不支持的数据源: {source}")
        if policy not in (DIRECT, VPN):
            raise ValueError(f"不支持的路由策略: {policy}")
        next_policies[source] = policy
    with _state_lock:
        _route_policies.clear()
        _route_policies.update(next_policies)
    db = await get_db()
    await db.execute(
        "INSERT OR REPLACE INTO runtime_settings (key, value) VALUES (?, ?)",
        (ROUTE_POLICY_KEY, json.dumps(next_policies, ensure_ascii=False)),
    )
    await db.commit()
    return next_policies


def build_route_env(source: str, base_env: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(base_env or os.environ)
    if get_route_policies().get(source, DIRECT) == VPN:
        for key in _PROXY_ENV_KEYS:
            env[key] = VPN_PROXY_URL
    else:
        for key in _PROXY_ENV_KEYS:
            env.pop(key, None)
    return env


@contextmanager
def outbound_route_env(source: str) -> Iterator[None]:
    with _env_lock:
        previous_values = {key: os.environ.get(key) for key in _PROXY_ENV_KEYS}
        try:
            updated_env = build_route_env(source)
            for key in _PROXY_ENV_KEYS:
                value = updated_env.get(key)
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
            yield
        finally:
            for key, previous_value in previous_values.items():
                if previous_value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = previous_value
