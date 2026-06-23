import os

from app.services import market_fetcher
from app.services.network_proxy_state import VPN_PROXY_URL, get_proxy_state, set_proxy_state


def test_agent_browser_cli_passes_proxy_env_when_enabled(monkeypatch):
    previous_state = get_proxy_state()["vpn_enabled"]
    captured: dict = {}

    class DummyResult:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def fake_run(cmd, capture_output, env, text, timeout):
        captured["cmd"] = cmd
        captured["env"] = env
        captured["timeout"] = timeout
        return DummyResult()

    try:
        set_proxy_state(True)
        monkeypatch.setattr(market_fetcher.subprocess, "run", fake_run)

        stdout = market_fetcher._agent_browser_cli("open", "https://example.com")

        assert stdout == "ok"
        assert captured["env"]["HTTP_PROXY"] == VPN_PROXY_URL
        assert captured["env"]["HTTPS_PROXY"] == VPN_PROXY_URL
    finally:
        set_proxy_state(previous_state)


def test_fetch_us_stock_wraps_akshare_call_with_proxy_env(monkeypatch):
    previous_state = get_proxy_state()["vpn_enabled"]
    captured: dict = {}

    class DummyDataFrame:
        empty = False

        def __len__(self):
            return 2

        @property
        def iloc(self):
            rows = [
                {"close": 99.5, "date": "2026-06-22"},
                {"close": 101.0, "date": "2026-06-23"},
            ]

            class _ILoc:
                def __getitem__(self, index):
                    return rows[index]

            return _ILoc()

    def fake_index_us_stock_sina(symbol):
        captured["symbol"] = symbol
        captured["HTTP_PROXY"] = os.environ.get("HTTP_PROXY")
        captured["HTTPS_PROXY"] = os.environ.get("HTTPS_PROXY")
        return DummyDataFrame()

    try:
        set_proxy_state(True)
        monkeypatch.setattr(market_fetcher.ak, "index_us_stock_sina", fake_index_us_stock_sina)

        result = market_fetcher.fetch_us_stock("tsla")

        assert result is not None
        assert captured["symbol"] == "TSLA"
        assert captured["HTTP_PROXY"] == VPN_PROXY_URL
        assert captured["HTTPS_PROXY"] == VPN_PROXY_URL
    finally:
        set_proxy_state(previous_state)
