"""證交所的離線測試：樣本是 2026-07-31 從 TWSE 實際抓回來的 JSON（大檔有截短）。"""
import json
from pathlib import Path

import pandas as pd
import pytest

from twchips._core import json_table

DATA = Path(__file__).parent / "data"


def _load(name):
    return json.load(open(DATA / name, encoding="utf-8"))


def test_bfi82u_institutional_summary():
    df = json_table(_load("twse_bfi82u_20260731.json"))
    assert len(df) == 6  # 自營商×2、投信、外資×2、合計
    total = df[df["單位名稱"] == "合計"].iloc[0]
    assert total["買賣差額"] == 87314410814
    hedge = df[df["單位名稱"] == "自營商(避險)"].iloc[0]
    assert hedge["買賣差額"] == -22000243211  # 負數帶千分位也要轉對


def test_t86_stock_id_stays_text():
    df = json_table(_load("twse_t86_20260731.json"))
    tsmc = df[df["證券代號"] == "2330"].iloc[0]
    assert tsmc["證券名稱"] == "台積電"  # 原始資料有尾空白，要被 strip
    assert tsmc["三大法人買賣超股數"] == 23568654
    assert not pd.api.types.is_numeric_dtype(df["證券代號"])  # 代號是文字，不能變成數字 2330


def test_margin_duplicate_columns_get_prefixed():
    tables = _load("twse_margn_20260731.json")["tables"]
    df = json_table(tables[1])
    # 融資、融券各有一組「買進／賣出…」，groups 前綴要把它們分開
    assert "融資買進" in df.columns and "融券買進" in df.columns
    assert len(df.columns) == len(set(df.columns))  # 不能有撞名
    tsmc = df[df["代號"] == "2330"].iloc[0]
    assert tsmc["融資今日餘額"] == 29289
    assert tsmc["融券今日餘額"] == 124


def test_margin_market_summary():
    tables = _load("twse_margn_20260731.json")["tables"]
    df = json_table(tables[0])
    assert list(df["項目"]) == ["融資(交易單位)", "融券(交易單位)", "融資金額(仟元)"]
    assert pd.api.types.is_numeric_dtype(df["今日餘額"])


def test_twse_who_shortcuts_are_bound():
    from twchips import twse

    for alias in ("foreign", "trust", "dealer"):
        assert getattr(twse.institutional, alias).keywords == {"who": alias}
