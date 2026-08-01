"""證交所（TWSE）：三大法人與融資融券。

證交所對狂打的 IP 會直接封鎖，抓歷史資料的迴圈記得 sleep。
"""
from __future__ import annotations

import pandas as pd

from ._core import get_json, json_table, norm_date_compact, who_shortcuts

_BASE = "https://www.twse.com.tw/rwd/zh/"

# BFI82U 的身份別比期交所細：自營商拆自行買賣／避險，外資拆陸資／外資自營商。
# who 用開頭比對，所以 foreign、dealer 會回兩列，照證交所原樣不幫你加總。
_WHO_PREFIX = {
    "foreign": "外資",
    "trust": "投信",
    "dealer": "自營商",
    "外資": "外資",
    "投信": "投信",
    "自營商": "自營商",
}


@who_shortcuts
def institutional(date, who: str | None = None) -> pd.DataFrame:
    """三大法人買賣金額統計（整體市場）。單位：元。

    列：自營商(自行買賣)、自營商(避險)、投信、外資及陸資(不含外資自營商)、
    外資自營商、合計。who 給 "foreign"／"trust"／"dealer"（中文也收）；
    institutional.foreign(date) 是縮寫。注意 foreign 和 dealer 各會回兩列。
    """
    payload = get_json(_BASE + "fund/BFI82U",
                       {"response": "json", "dayDate": norm_date_compact(date), "type": "day"})
    df = _table_or_empty(payload)
    if who is None or df.empty:
        return df
    if who not in _WHO_PREFIX:
        raise ValueError(f"who 要是 foreign／trust／dealer（或中文），收到 {who!r}")
    return df[df["單位名稱"].str.startswith(_WHO_PREFIX[who])].reset_index(drop=True)


def institutional_stocks(date, stock: str | None = None) -> pd.DataFrame:
    """個股三大法人買賣超（全市場每一檔）。單位：股。

    stock -- 證券代號，例如 "2330"，只要那一檔。
    欄位是寬表：外陸資、外資自營商、投信、自營商（自行買賣／避險）各自的
    買進、賣出、買賣超，最後一欄是三大法人合計買賣超。
    """
    payload = get_json(_BASE + "fund/T86",
                       {"response": "json", "date": norm_date_compact(date),
                        "selectType": "ALLBUT0999"})
    df = _table_or_empty(payload)
    if stock is not None and not df.empty:
        df = df[df["證券代號"] == stock].reset_index(drop=True)
    return df


def margin(date) -> pd.DataFrame:
    """信用交易統計（整體市場）：融資、融券的買進賣出與餘額，三列。"""
    return _margin_tables(date)[0]


def margin_stocks(date, stock: str | None = None) -> pd.DataFrame:
    """個股融資融券餘額（全市場每一檔）。

    融資、融券的同名欄位已加前綴分開（融資買進、融券買進…）。
    stock -- 代號，例如 "2330"。
    """
    df = _margin_tables(date)[1]
    if stock is not None and not df.empty:
        df = df[df["代號"] == stock].reset_index(drop=True)
    return df


def _margin_tables(date) -> tuple[pd.DataFrame, pd.DataFrame]:
    payload = get_json(_BASE + "marginTrading/MI_MARGN",
                       {"response": "json", "date": norm_date_compact(date),
                        "selectType": "ALL"})
    if payload.get("stat") != "OK" or not payload.get("tables"):
        return pd.DataFrame(), pd.DataFrame()
    tables = payload["tables"]
    return json_table(tables[0]), json_table(tables[1])


def _table_or_empty(payload: dict) -> pd.DataFrame:
    # 非交易日 stat 會是「很抱歉，沒有符合條件的資料!」
    if payload.get("stat") != "OK":
        return pd.DataFrame()
    return json_table(payload)
