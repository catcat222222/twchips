"""離線測試：樣本是 2026-07-31 從期交所實際抓回來的原始回應（Big5）。"""
from pathlib import Path

import pandas as pd
import pytest

from taifex_daily import _filter_session, _parse

DATA = Path(__file__).parent / "data"


@pytest.fixture
def fut():
    return _parse((DATA / "fut_20260731.csv").read_bytes())


@pytest.fixture
def opt():
    return _parse((DATA / "opt_20260731_head.csv").read_bytes())


def test_futures_columns_aligned(fut):
    # 期貨檔行尾多逗號，這裡驗證欄位沒有位移
    row = fut.iloc[0]
    assert row["契約"] == "TX"
    assert row["交易時段"] == "一般"
    assert row["收盤價"] == 43678
    assert row["結算價"] == 43727


def test_expiry_month_kept_as_text(fut):
    # "202608  " 要去空白、而且不能被轉成數字
    assert fut.iloc[0]["到期月份(週別)"] == "202608"


def test_numeric_conversion(fut):
    assert fut["收盤價"].dtype == "float64"
    assert fut.iloc[0]["漲跌%"] == pytest.approx(8.42)
    assert fut["未沖銷契約數"].notna().any()


def test_dash_becomes_na(fut):
    # 盤後時段沒有結算價，原始值是 "-"
    after_hours = fut[fut["交易時段"] == "盤後"]
    assert after_hours["結算價"].isna().all()


def test_session_filter(fut):
    regular = _filter_session(fut, "regular")
    assert set(regular["交易時段"]) == {"一般"}
    assert len(regular) < len(fut)
    with pytest.raises(ValueError):
        _filter_session(fut, "盤前")


def test_options_chain(opt):
    assert set(opt["買賣權"]) <= {"買權", "賣權"}
    assert opt["履約價"].dtype == "float64"
    assert (opt["契約"] == "TXO").all()


def test_non_trading_day_is_empty():
    df = _parse((DATA / "fut_sunday.csv").read_bytes())
    assert df.empty
    assert "交易日期" in df.columns
    assert _filter_session(df, "regular").empty
