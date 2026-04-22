"""
行情抓取模块 - 获取各市场行情数据

支持的行情类型：
- 港股：agent-browser 富途网页爬取（fallback: stock_hk_hist_min_em）
- A股/ETF：fund_etf_spot_em / stock_zh_a_spot_em
- 场外基金：fund_open_fund_info_em
- 汇率：fx_spot_quote
"""

import logging
import platform
import re
import subprocess
import time
from datetime import datetime, timedelta

import akshare as ak
import pandas as pd

from app.core.config import get_settings
from app.repositories import price_repo

logger = logging.getLogger(__name__)
settings = get_settings()

FUND_DAILY_CACHE_TTL_SECONDS = 3600
_fund_daily_cache_df: pd.DataFrame | None = None
_fund_daily_cache_expires_at: float = 0.0


def _fetch_hk_stock_akshare(code: str) -> dict | None:
    """
    通过 AKShare 获取港股价格
    :param code: 港股代码，如 "00700"
    :return: {"price": float, "price_date": str, "currency": "HKD", "growth_rate": float} 或 None
    """
    try:
        start_date = datetime.now() - timedelta(days=3)
        df = ak.stock_hk_hist_min_em(symbol=code, start_date=start_date.strftime("%Y-%m-%d %H:%M:%S"))
        if df.empty:
            logger.warning(f"港股 {code} 未找到行情数据")
            return None
        row = df.iloc[-1]
        latest_price = float(row["收盘"])
        price_date = str(row["时间"])[:10]
        # 计算日增长率：用最后一条和倒数第二条的收盘价
        if len(df) >= 2:
            prev_close = float(df.iloc[-2]["收盘"])
            growth_rate = (latest_price - prev_close) / prev_close if prev_close != 0 else 0.0
        else:
            growth_rate = 0.0
        return {
            "price": latest_price,
            "price_date": price_date,
            "currency": "HKD",
            "growth_rate": growth_rate,
        }
    except Exception as e:
        logger.error(f"AKShare 获取港股 {code} 行情失败: {e}")
        return None


def _agent_browser_cli(*args: str) -> str:
    """调用全局 agent-browser CLI，Linux 下附加 no-sandbox 参数"""
    cmd = ["agent-browser"]
    if platform.system() == "Linux":
        cmd.extend(["--args", "--no-sandbox"])
    cmd.extend(args)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=settings.MARKET_FETCH_TIMEOUT,
    )
    if result.returncode != 0:
        raise RuntimeError(f"agent-browser 命令失败: {result.stderr.strip()}")
    return result.stdout.strip()


def _fetch_hk_stock_browser(code: str) -> dict | None:
    """
    通过 agent-browser 访问富途港股页面获取价格
    :param code: 港股代码，如 "00700"
    :return: {"price": float, "price_date": str, "currency": "HKD", "growth_rate": float} 或 None
    """
    try:
        # 1. 打开富途港股行情页
        url = f"https://www.futunn.com/stock/{code}-HK"
        _agent_browser_cli("open", url)

        # 2. 等待页面加载
        time.sleep(3)

        # 3. 获取页面快照文本
        snap_text = _agent_browser_cli("snapshot")

        # 4. 用富途页面结构提取最新价和涨幅
        pattern = (
            r'- StaticText "添加自选"\s+'
            r'- list\s+'
            r'- listitem \[level=1\]\s+'
            r'- StaticText "(\d+(?:\.\d+)?)"\s+'
            r'- listitem \[level=1\]\s+\s+'
            r'- StaticText "[+-]?\d+(?:\.\d+)?[+-](\d+(?:\.\d+)?)%"'
        )
        match = re.search(pattern, snap_text, re.DOTALL)
        if not match:
            logger.warning(f"浏览器抓取未在页面快照中找到港股 {code} 的价格与日增长率")
            return None

        latest_price = float(match.group(1))
        growth_rate = float(match.group(2)) / 100  # 页面显示百分比，转为小数
        return {
            "price": latest_price,
            "price_date": datetime.now().strftime("%Y-%m-%d"),
            "currency": "HKD",
            "growth_rate": growth_rate,
        }
    except FileNotFoundError:
        logger.warning("agent-browser 命令未找到，浏览器 fallback 不可用")
        return None
    except subprocess.TimeoutExpired:
        logger.error(f"agent-browser 获取港股 {code} 行情超时")
        return None
    except Exception as e:
        logger.error(f"浏览器获取港股 {code} 行情失败: {e}")
        return None
    finally:
        try:
            _agent_browser_cli("close")
        except Exception:
            pass


def fetch_hk_stock(code: str) -> dict | None:
    """
    获取港股价格
    优先使用 agent-browser 爬取富途网页，失败时 fallback 到 AKShare
    :param code: 港股代码，如 "00700"
    :return: {"price": float, "price_date": str, "currency": "HKD", "growth_rate": float} 或 None
    """
    result = _fetch_hk_stock_browser(code)
    if result is not None:
        return result

    logger.info(f"港股 {code} 浏览器抓取失败，尝试 AKShare fallback")
    return _fetch_hk_stock_akshare(code)


def fetch_a_etf(code: str) -> dict | None:
    """
    获取 A 股/ETF 价格
    :param code: 证券代码，如 "510300"
    :return: {"price": float, "price_date": str, "currency": "CNY", "growth_rate": float} 或 None
    """
    try:
        # 先尝试 ETF
        if code.startswith(("51", "15", "16", "50", "52", "56", "58")):
            df = ak.fund_etf_spot_em()
            row = df[df["代码"] == code]
            if not row.empty:
                latest_price = float(row.iloc[0]["最新价"])
                growth_rate = float(row.iloc[0].get("涨跌幅", 0)) / 100 if "涨跌幅" in df.columns else 0.0
                return {
                    "price": latest_price,
                    "price_date": datetime.now().strftime("%Y-%m-%d"),
                    "currency": "CNY",
                    "growth_rate": growth_rate,
                }
        # 再尝试 A 股
        df = ak.stock_zh_a_spot_em()
        row = df[df["代码"] == code]
        if not row.empty:
            latest_price = float(row.iloc[0]["最新价"])
            growth_rate = float(row.iloc[0].get("涨跌幅", 0)) / 100 if "涨跌幅" in df.columns else 0.0
            return {
                "price": latest_price,
                "price_date": datetime.now().strftime("%Y-%m-%d"),
                "currency": "CNY",
                "growth_rate": growth_rate,
            }
        logger.warning(f"A股/ETF {code} 未找到行情数据")
        return None
    except Exception as e:
        logger.error(f"获取 A股/ETF {code} 行情失败: {e}")
        return None


async def fetch_fund_nav(code: str) -> dict | None:
    """
    获取场外基金净值
    :param code: 基金代码，如 "000001"
    :return: {"price": float, "price_date": str, "currency": "CNY", "growth_rate": float} 或 None
    """
    try:
        df = _get_fund_open_fund_daily_df()
        if df.empty:
            logger.warning(f"基金 {code} 未找到净值数据")
            return None

        fund_row = df[df["基金代码"].astype(str).str.zfill(6) == str(code).zfill(6)]
        if fund_row.empty:
            logger.warning(f"基金 {code} 未在日净值总表中找到")
            return None

        row = fund_row.iloc[0]
        nav_columns: list[tuple[str, str]] = []
        for column in df.columns:
            match = re.fullmatch(r"(\d{4}-\d{2}-\d{2})-单位净值", str(column))
            if match:
                nav_columns.append((match.group(1), column))

        nav_columns.sort(key=lambda item: item[0], reverse=True)

        nav = None
        nav_date = None
        previous_nav = None
        for date_str, column in nav_columns:
            value = row.get(column)
            if pd.isna(value) or value == "":
                continue

            try:
                numeric_value = float(value)
            except (ValueError, TypeError):
                continue

            if nav is None:
                nav = numeric_value
                nav_date = date_str
            else:
                previous_nav = numeric_value
                break

        if nav is None or nav_date is None:
            logger.warning(f"基金 {code} 未找到有效单位净值")
            return None

        if previous_nav is None:
            previous_price = await price_repo.get_previous_price(str(code).zfill(6), nav_date)
            if previous_price is not None:
                try:
                    previous_nav = float(previous_price["price"])
                except (ValueError, TypeError, KeyError):
                    previous_nav = None

        growth_rate = 0.0
        if previous_nav is not None and previous_nav != 0:
            growth_rate = (nav - previous_nav) / previous_nav

        return {
            "price": nav,
            "price_date": nav_date,
            "currency": "CNY",
            "growth_rate": growth_rate,
        }
    except Exception as e:
        logger.error(f"获取基金 {code} 净值失败: {e}")
        return None


def _get_fund_open_fund_daily_df(force_refresh: bool = False) -> pd.DataFrame:
    """获取场外基金日净值总表，使用进程内 1 小时缓存降低 AKShare 调用频率。"""
    global _fund_daily_cache_df, _fund_daily_cache_expires_at

    now = time.time()
    if (
        not force_refresh
        and _fund_daily_cache_df is not None
        and now < _fund_daily_cache_expires_at
    ):
        return _fund_daily_cache_df

    logger.info("刷新基金日净值总表缓存")
    df = ak.fund_open_fund_daily_em()
    _fund_daily_cache_df = df
    _fund_daily_cache_expires_at = now + FUND_DAILY_CACHE_TTL_SECONDS
    return df


def invalidate_fund_nav_cache() -> None:
    """手动清空场外基金日净值总表缓存。"""
    global _fund_daily_cache_df, _fund_daily_cache_expires_at

    _fund_daily_cache_df = None
    _fund_daily_cache_expires_at = 0.0


def fetch_hkdcny_rate() -> dict | None:
    """
    获取 HKD/CNY 汇率
    :return: {"rate": float, "rate_date": str} 或 None
    """
    try:
        df = ak.fx_spot_quote()
        row = df[df["货币对"] == "HKD/CNY"]
        if row.empty:
            logger.warning("未找到 HKD/CNY 汇率数据")
            return None
        # 中行折算价作为汇率
        row = row.iloc[0]
        rate = (row['买报价'] + row['卖报价']) / 2
        return {
            "rate": rate,
            "rate_date": datetime.now().strftime("%Y-%m-%d"),
        }
    except Exception as e:
        logger.error(f"获取 HKD/CNY 汇率失败: {e}")
        return None
