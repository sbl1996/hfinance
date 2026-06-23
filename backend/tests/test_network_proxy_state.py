import os
from contextlib import ExitStack

from app.services.network_proxy_state import (
    VPN_PROXY_URL,
    build_proxy_env,
    get_proxy_state,
    outbound_proxy_env,
    set_proxy_state,
)


def test_proxy_state_defaults_to_disabled():
    state = get_proxy_state()
    assert state == {"vpn_enabled": False, "proxy_url": VPN_PROXY_URL}


def test_build_proxy_env_adds_proxy_when_enabled():
    previous_state = get_proxy_state()["vpn_enabled"]
    try:
        set_proxy_state(True)
        env = build_proxy_env({"PATH": "/tmp/bin"})
        assert env["HTTP_PROXY"] == VPN_PROXY_URL
        assert env["HTTPS_PROXY"] == VPN_PROXY_URL
        assert env["http_proxy"] == VPN_PROXY_URL
        assert env["https_proxy"] == VPN_PROXY_URL
    finally:
        set_proxy_state(previous_state)


def test_build_proxy_env_removes_proxy_when_disabled():
    previous_state = get_proxy_state()["vpn_enabled"]
    try:
        set_proxy_state(False)
        env = build_proxy_env(
            {
                "HTTP_PROXY": VPN_PROXY_URL,
                "HTTPS_PROXY": VPN_PROXY_URL,
                "http_proxy": VPN_PROXY_URL,
                "https_proxy": VPN_PROXY_URL,
                "PATH": "/tmp/bin",
            }
        )
        assert "HTTP_PROXY" not in env
        assert "HTTPS_PROXY" not in env
        assert "http_proxy" not in env
        assert "https_proxy" not in env
        assert env["PATH"] == "/tmp/bin"
    finally:
        set_proxy_state(previous_state)


def test_outbound_proxy_env_applies_and_restores_environment(monkeypatch):
    previous_state = get_proxy_state()["vpn_enabled"]
    try:
        monkeypatch.delenv("HTTP_PROXY", raising=False)
        monkeypatch.delenv("HTTPS_PROXY", raising=False)
        monkeypatch.delenv("http_proxy", raising=False)
        monkeypatch.delenv("https_proxy", raising=False)

        set_proxy_state(True)
        with outbound_proxy_env():
            assert os.environ["HTTP_PROXY"] == VPN_PROXY_URL
            assert os.environ["HTTPS_PROXY"] == VPN_PROXY_URL

        for key in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
            assert key not in os.environ
    finally:
        set_proxy_state(previous_state)
