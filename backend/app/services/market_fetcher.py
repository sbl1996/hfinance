"""
行情抓取模块 - 调用 AKShare 获取各市场行情数据

支持的行情类型：
- 港股：stock_hk_hist_min_em（fallback: ocbrowser 东方财富网页爬取）
- A股/ETF：fund_etf_spot_em / stock_zh_a_spot_em
- 场外基金：fund_open_fund_info_em
- 汇率：fx_spot_quote
"""

import json
import logging
import re
import subprocess
import time
from datetime import datetime, timedelta

import akshare as ak

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


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


def _ocbrowser_cli(*args: str, json_output: bool = False) -> str:
    """调用 ocbrowser CLI 命令，返回 stdout 文本"""
    cmd = ["ocbrowser"]
    if json_output:
        cmd.append("--json")
    cmd.extend(args)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=settings.MARKET_FETCH_TIMEOUT,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ocbrowser 命令失败: {result.stderr.strip()}")
    return result.stdout.strip()


def _fetch_hk_stock_browser(code: str) -> dict | None:
    """
    通过 ocbrowser 访问东方财富港股页面获取价格（fallback 方式）
    :param code: 港股代码，如 "00700"
    :return: {"price": float, "price_date": str, "currency": "HKD", "growth_rate": float} 或 None
    """
    target_id = None
    try:
        # 1. 打开东方财富港股行情页
        url = f"https://quote.eastmoney.com/hk/{code}.html"
        open_output = _ocbrowser_cli("open", url, json_output=True)
        open_result = json.loads(open_output)
        target_id = open_result.get("targetId")
        if not target_id:
            logger.error("ocbrowser 打开港股页面失败，未获取到 targetId")
            return None

        # 2. 等待页面加载
        time.sleep(3)

        # 3. 获取页面快照
        snap_text = _ocbrowser_cli("snapshot", "--target-id", target_id)

        # 4. 用正则提取最新价
        price_match = re.search(r"最新[：:]\s*(\d+\.\d+)", snap_text)
        if not price_match:
            logger.warning(f"浏览器 fallback 未在页面快照中找到港股 {code} 的最新价")
            return None
        growth_match = re.search(r"涨幅[：:]\s*([\d\.-]+)", snap_text)
        if not growth_match:
            logger.warning(f"浏览器 fallback 未在页面快照中找到港股 {code} 的日增长率")
            return None

        latest_price = float(price_match.group(1))
        growth_rate = float(growth_match.group(1)) / 100  # 页面显示百分比，转为小数
        return {
            "price": latest_price,
            "price_date": datetime.now().strftime("%Y-%m-%d"),
            "currency": "HKD",
            "growth_rate": growth_rate,
        }
    except FileNotFoundError:
        logger.warning("ocbrowser 命令未找到，浏览器 fallback 不可用")
        return None
    except subprocess.TimeoutExpired:
        logger.error(f"ocbrowser 获取港股 {code} 行情超时")
        return None
    except Exception as e:
        logger.error(f"浏览器 fallback 获取港股 {code} 行情失败: {e}")
        return None
    finally:
        # 5. 关闭页面
        if target_id:
            try:
                _ocbrowser_cli("close", target_id)
            except Exception:
                pass


def fetch_hk_stock(code: str) -> dict | None:
    """
    获取港股价格
    优先使用 AKShare，失败时 fallback 到 ocbrowser 爬取东方财富网页
    :param code: 港股代码，如 "00700"
    :return: {"price": float, "price_date": str, "currency": "HKD", "growth_rate": float} 或 None
    """
    result = _fetch_hk_stock_akshare(code)
    if result is not None:
        return result

    logger.info(f"港股 {code} AKShare 获取失败，尝试浏览器 fallback")
    return _fetch_hk_stock_browser(code)


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


def fetch_fund_nav(code: str) -> dict | None:
    """
    获取场外基金净值
    :param code: 基金代码，如 "000001"
    :return: {"price": float, "price_date": str, "currency": "CNY", "growth_rate": float} 或 None
    """
    try:
        df = ak.fund_open_fund_info_em(symbol=code)
        if df.empty:
            logger.warning(f"基金 {code} 未找到净值数据")
            return None
        # 取最后一行
        last_row = df.iloc[-1]
        nav = float(last_row["单位净值"])
        nav_date = str(last_row["净值日期"])[:10]
        # 日增长率
        if "日增长率" in df.columns and len(df) >= 2:
            growth_str = last_row["日增长率"]
            try:
                growth_rate = float(growth_str) / 100
            except (ValueError, TypeError):
                growth_rate = 0.0
        elif len(df) >= 2:
            prev_nav = float(df.iloc[-2]["单位净值"])
            growth_rate = (nav - prev_nav) / prev_nav if prev_nav != 0 else 0.0
        else:
            growth_rate = 0.0
        return {
            "price": nav,
            "price_date": nav_date,
            "currency": "CNY",
            "growth_rate": growth_rate,
        }
    except Exception as e:
        logger.error(f"获取基金 {code} 净值失败: {e}")
        return None


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
