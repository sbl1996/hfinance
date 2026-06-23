"""Runtime VPN proxy state and helpers for outbound HTTP/HTTPS fetches."""

from __future__ import annotations

import os
from contextlib import contextmanager
from threading import Lock
from typing import Iterator

VPN_PROXY_URL = "http://127.0.0.1:7890"
_PROXY_ENV_KEYS = ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy")

_vpn_enabled = False
_state_lock = Lock()


def get_proxy_state() -> dict[str, str | bool]:
    with _state_lock:
        enabled = _vpn_enabled
    return {
        "vpn_enabled": enabled,
        "proxy_url": VPN_PROXY_URL,
    }


def set_proxy_state(enabled: bool) -> dict[str, str | bool]:
    global _vpn_enabled
    with _state_lock:
        _vpn_enabled = bool(enabled)
        enabled_value = _vpn_enabled
    return {
        "vpn_enabled": enabled_value,
        "proxy_url": VPN_PROXY_URL,
    }


def build_proxy_env(base_env: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(base_env or os.environ)
    state = get_proxy_state()
    if state["vpn_enabled"]:
        for key in _PROXY_ENV_KEYS:
            env[key] = VPN_PROXY_URL
    else:
        for key in _PROXY_ENV_KEYS:
            env.pop(key, None)
    return env


@contextmanager
def outbound_proxy_env() -> Iterator[None]:
    previous_values = {key: os.environ.get(key) for key in _PROXY_ENV_KEYS}
    try:
        updated_env = build_proxy_env()
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
