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


def test_agent_browser_cli_retries_failed_connection(monkeypatch):
    calls = 0
    sleeps: list[int] = []

    class FailedResult:
        returncode = 1
        stdout = ""
        stderr = "Could not configure browser: Failed to connect: No such file or directory"

    class SuccessResult:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def fake_run(*args, **kwargs):
        nonlocal calls
        calls += 1
        return FailedResult() if calls < 3 else SuccessResult()

    monkeypatch.setattr(market_fetcher.subprocess, "run", fake_run)
    monkeypatch.setattr(market_fetcher.time, "sleep", sleeps.append)

    assert market_fetcher._agent_browser_cli("open", "https://example.com") == "ok"
    assert calls == 3
    assert sleeps == [market_fetcher.AGENT_BROWSER_CONNECT_RETRY_SECONDS] * 2


def test_fetch_cn_index_eastmoney_parses_after_hours_layout(monkeypatch):
    snapshot = '''
        - generic
          - StaticText "红利低波"
          - StaticText "H30269"
          - emphasis
          - StaticText "10607.56"
          - StaticText "-102.21-0.95%"
    '''

    monkeypatch.setattr(market_fetcher.time, "sleep", lambda _: None)
    monkeypatch.setattr(
        market_fetcher,
        "_agent_browser_cli",
        lambda command, *args: snapshot if command == "snapshot" else "",
    )

    result = market_fetcher._fetch_cn_index_eastmoney("H30269")

    assert result is not None
    assert result["price"] == 10607.56


def test_fetch_cn_index_yahoo_parses_quote_snapshot(monkeypatch):
    snapshot = '''
        - StaticText "Shanghai - Delayed Quote"
        - StaticText "CNY"
        - heading "CSI Dividend Low Volatility Ind (H30269.SS)" [level=1]
        - StaticText "10,975.80"
        - StaticText "+117.03"
        - StaticText "(+1.08%)"
        - StaticText "At close: 3:00:24 PM GMT+8"
    '''

    monkeypatch.setattr(market_fetcher.time, "sleep", lambda _: None)
    monkeypatch.setattr(
        market_fetcher,
        "_agent_browser_cli",
        lambda command, *args: snapshot if command == "snapshot" else "",
    )

    result = market_fetcher._fetch_cn_index_yahoo("H30269")

    assert result is not None
    assert result["price"] == 10975.8
    assert result["currency"] == "CNY"
    assert result["growth_rate"] == 0.0108


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
