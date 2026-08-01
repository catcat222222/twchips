"""三大法人的離線測試：樣本是 2026-07-31 從期交所實際抓回來的原始回應（Big5）。"""
from pathlib import Path

import pytest

from twchips._core import parse_big5_csv

DATA = Path(__file__).parent / "data"


@pytest.fixture
def total():
    return parse_big5_csv((DATA / "institutional_total_20260731.csv").read_bytes())


def test_total_matches_website(total):
    # 對照期交所網站總表頁 2026/07/31 的數字
    assert len(total) == 3  # 自營商、投信、外資及陸資；CSV 沒有合計列
    dealer = total[total["身份別"] == "自營商"].iloc[0]
    assert dealer["多方交易口數"] == 284710
    assert dealer["多空交易契約金額淨額(百萬元)"] == -25736
    assert dealer["多空未平倉口數淨額"] == -258493
    foreign = total[total["身份別"] == "外資及陸資"].iloc[0]
    assert foreign["多空交易口數淨額"] == -937


def test_total_negative_numbers_are_numeric(total):
    assert total["多空未平倉契約金額淨額(百萬元)"].dtype == "float64"
    assert (total["多空未平倉口數淨額"] < 0).any()


def test_futures_by_product():
    df = parse_big5_csv((DATA / "institutional_fut_20260731.csv").read_bytes())
    assert "臺股期貨" in set(df["商品名稱"])
    assert set(df["身份別"]) == {"自營商", "投信", "外資及陸資"}
    # 依商品的金額單位是千元，欄名要跟總表（百萬元）分得開
    assert "多方交易契約金額(千元)" in df.columns


def test_options_calls_and_puts():
    df = parse_big5_csv((DATA / "institutional_opt_20260731.csv").read_bytes())
    assert set(df["買賣權別"]) == {"CALL", "PUT"}
    assert df["買方交易口數"].dtype == "float64"
