"""持仓止盈止损预警评估与飞书通知。"""

import asyncio
import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.repositories import holding_alert_repo, holding_repo
from app.services.currency_service import get_latest_cny_rate_map

logger = logging.getLogger(__name__)
settings = get_settings()
APP_TZ = ZoneInfo(settings.APP_TIMEZONE)


def select_warning_type(
    pnl_rate: float,
    take_profit_rate: float | None,
    stop_loss_rate: float | None,
) -> str | None:
    if take_profit_rate is not None and pnl_rate >= take_profit_rate:
        return "TAKE_PROFIT"
    if stop_loss_rate is not None and pnl_rate <= stop_loss_rate:
        return "STOP_LOSS"
    return None


def _format_rate(value: float) -> str:
    prefix = "+" if value > 0 else ""
    return f"{prefix}{value * 100:.2f}%"


def _build_feishu_message(
    holding: dict,
    warning_type: str,
    pnl_rate: float,
    threshold: float,
    price: float,
    price_currency: str,
    triggered_at: str,
) -> str:
    warning_label = "止盈" if warning_type == "TAKE_PROFIT" else "止损"
    return "\n".join(
        [
            f"【HFinance {warning_label}提醒】",
            "",
            f"{holding['name']}（{holding['code']}）",
            f"累计收益率：{_format_rate(pnl_rate)}",
            f"{warning_label}线：{_format_rate(threshold)}",
            f"最新价：{price:g} {price_currency}",
            f"触发时间：{triggered_at}",
            "",
            "该持仓可能需要卖出处理。",
        ]
    )


async def _send_feishu_webhook(message: str) -> tuple[str, str | None]:
    webhook_url = settings.FEISHU_WEBHOOK_URL.strip()
    if not webhook_url:
        logger.warning("持仓预警已触发，但未配置 HFINANCE_FEISHU_WEBHOOK_URL")
        return "DISABLED", "未配置飞书 Webhook URL"

    payload = json.dumps(
        {"msg_type": "text", "content": {"text": message}},
        ensure_ascii=False,
    )
    try:
        process = await asyncio.create_subprocess_exec(
            "curl",
            "-fsS",
            "--max-time",
            str(settings.ALERT_WEBHOOK_TIMEOUT_SECONDS),
            "-X",
            "POST",
            "-H",
            "Content-Type: application/json",
            "--data",
            payload,
            webhook_url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
    except Exception as exc:
        logger.exception("调用飞书预警 Webhook 失败")
        return "FAILED", str(exc)

    response_text = stdout.decode(errors="replace").strip()
    if process.returncode == 0:
        try:
            response_data = json.loads(response_text) if response_text else {}
        except json.JSONDecodeError:
            response_data = {}
        response_code = response_data.get("code", response_data.get("StatusCode", 0))
        if response_code in (0, None):
            logger.info("飞书持仓预警发送成功: %s", response_text)
            return "SUCCESS", None
        error = response_data.get("msg") or response_data.get("StatusMessage") or response_text
        logger.error("飞书持仓预警被拒绝: %s", error)
        return "FAILED", str(error)[:1000]

    error = stderr.decode(errors="replace").strip() or f"curl exit code {process.returncode}"
    logger.error("飞书持仓预警发送失败: %s", error)
    return "FAILED", error[:1000]


async def evaluate_holding_alerts(
    *,
    code: str,
    market: str,
    price: float,
    price_currency: str,
) -> list[dict]:
    """按一次成功刷新的实时价格评估该标的下所有持仓。"""
    holdings = await holding_repo.get_by_code_and_market(code, market)
    if not holdings:
        return []

    rate_map = await get_latest_cny_rate_map()
    cny_rate = rate_map.get(price_currency, 1.0)
    now = datetime.now(APP_TZ)
    trigger_date = now.strftime("%Y-%m-%d")
    triggered_at = now.strftime("%Y-%m-%d %H:%M:%S")
    triggered: list[dict] = []

    for holding in holdings:
        if not holding.get("alert_enabled") or holding.get("warning_active"):
            continue
        if holding.get("last_trigger_date") == trigger_date:
            continue
        cost_total = float(holding.get("cost_total_cny") or 0)
        if cost_total <= 0:
            continue

        market_value_cny = price * float(holding["quantity"]) * cny_rate
        pnl_rate = (market_value_cny - cost_total) / cost_total
        warning_type = select_warning_type(
            pnl_rate,
            holding.get("take_profit_rate"),
            holding.get("stop_loss_rate"),
        )
        if not warning_type:
            continue

        activated = await holding_alert_repo.activate_once_for_date(
            holding["id"],
            warning_type,
            triggered_at,
            trigger_date,
        )
        if not activated:
            continue

        threshold = (
            float(holding["take_profit_rate"])
            if warning_type == "TAKE_PROFIT"
            else float(holding["stop_loss_rate"])
        )
        message = _build_feishu_message(
            holding,
            warning_type,
            pnl_rate,
            threshold,
            price,
            price_currency,
            triggered_at,
        )
        webhook_status, webhook_error = await _send_feishu_webhook(message)
        await holding_alert_repo.update_webhook_result(
            holding["id"],
            webhook_status,
            webhook_error,
        )
        triggered.append(
            {
                "holding_id": holding["id"],
                "warning_type": warning_type,
                "pnl_rate": pnl_rate,
                "webhook_status": webhook_status,
            }
        )

    return triggered
