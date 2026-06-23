import pandas as pd

from app.models.schemas import IndexImportPrefixType
from app.services.fund_history_import_service import (
    build_cn_index_symbol,
    load_daily_closes_from_dataframe,
)


def test_build_cn_index_symbol_uses_lowercase_prefix_and_original_code():
    assert build_cn_index_symbol("H30269", IndexImportPrefixType.CSI) == "csih30269"
    assert build_cn_index_symbol("H30269", IndexImportPrefixType.SZ) == "szh30269"
    assert build_cn_index_symbol("H30269", IndexImportPrefixType.SH) == "shh30269"


def test_load_daily_closes_from_dataframe_reads_date_and_close():
    df = pd.DataFrame(
        [
            {"date": "2026-06-22", "close": 10501.47},
            {"date": "2026-06-23", "close": 10557.26},
        ]
    )

    assert load_daily_closes_from_dataframe(df) == {
        "2026-06-22": 10501.47,
        "2026-06-23": 10557.26,
    }
