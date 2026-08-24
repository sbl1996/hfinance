from app.services.holding_alert_service import select_warning_type


def test_selects_take_profit_at_threshold():
    assert select_warning_type(0.2, 0.2, -0.1) == "TAKE_PROFIT"


def test_selects_stop_loss_at_threshold():
    assert select_warning_type(-0.1, 0.2, -0.1) == "STOP_LOSS"


def test_does_not_trigger_inside_range():
    assert select_warning_type(0.05, 0.2, -0.1) is None


def test_supports_only_one_configured_threshold():
    assert select_warning_type(0.3, None, -0.1) is None
    assert select_warning_type(-0.2, 0.2, None) is None
