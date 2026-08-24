import os
from app.services.network_proxy_state import (
    DIRECT,
    VPN,
    VPN_PROXY_URL,
    build_route_env,
    get_route_policies,
    outbound_route_env,
)


def test_default_routes_use_vpn_only_for_yahoo():
    policies = get_route_policies()
    assert policies["YAHOO"] == VPN
    assert policies["EASTMONEY"] == DIRECT


def test_build_route_env_uses_explicit_policy():
    env = build_route_env("YAHOO", {"PATH": "/tmp/bin"})
    assert env["HTTP_PROXY"] == VPN_PROXY_URL
    assert env["HTTPS_PROXY"] == VPN_PROXY_URL

    direct_env = build_route_env("EASTMONEY", {"HTTP_PROXY": VPN_PROXY_URL, "PATH": "/tmp/bin"})
    assert "HTTP_PROXY" not in direct_env
    assert direct_env["PATH"] == "/tmp/bin"


def test_outbound_route_env_applies_and_restores_environment(monkeypatch):
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
        monkeypatch.delenv(key, raising=False)
    with outbound_route_env("YAHOO"):
        assert os.environ["HTTP_PROXY"] == VPN_PROXY_URL
        assert os.environ["HTTPS_PROXY"] == VPN_PROXY_URL
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
        assert key not in os.environ
