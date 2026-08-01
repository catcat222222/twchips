"""期交所（TAIFEX）：日行情與三大法人。"""
from __future__ import annotations

import pandas as pd

from ._core import filter_session, norm_date, post_csv, who_shortcuts

_BASE = "https://www.taifex.com.tw/cht/3/"

# 資料裡的正式名稱是「外資及陸資」；who= 收英文或中文都行
_WHO = {
    "foreign": "外資及陸資",
    "trust": "投信",
    "dealer": "自營商",
    "外資": "外資及陸資",
    "外資及陸資": "外資及陸資",
    "投信": "投信",
    "自營商": "自營商",
}


def _filter_who(df: pd.DataFrame, who: str | None) -> pd.DataFrame:
    if who is None or df.empty:
        return df
    if who not in _WHO:
        raise ValueError(f"who 要是 foreign／trust／dealer（或中文），收到 {who!r}")
    return df[df["身份別"] == _WHO[who]].reset_index(drop=True)


def _filter_eq(df: pd.DataFrame, col: str, value: str | None) -> pd.DataFrame:
    if value is None or df.empty:
        return df
    return df[df[col] == value].reset_index(drop=True)


def futures_daily(date, product: str = "TX", session: str | None = None) -> pd.DataFrame:
    """抓某一天的期貨日行情（開高低收、結算價、未沖銷契約數…）。

    date     -- "2026-07-31"、"2026/07/31" 或 datetime.date 都可以
    product  -- 商品代號，預設 TX（台指期）；MTX、TE、TF… 也通
    session  -- None＝全部；"regular"＝一般時段；"after_hours"＝盤後時段
    """
    df = _daily(_BASE + "futDataDown", product, date)
    return filter_session(df, session)


def options_daily(date, product: str = "TXO", session: str | None = None) -> pd.DataFrame:
    """抓某一天的選擇權日行情（整條鏈：履約價、買賣權、結算價…）。

    參數同 futures_daily，product 預設 TXO（台指選擇權）。
    """
    df = _daily(_BASE + "optDataDown", product, date)
    return filter_session(df, session)


@who_shortcuts
def institutional(date, who: str | None = None) -> pd.DataFrame:
    """三大法人「總表」：期貨＋選擇權合計的交易與未平倉，多空口數與契約金額。

    就是期交所網站三大法人專區第一頁那兩張表，攤平成一張。
    身份別：自營商、投信、外資及陸資。金額單位是「百萬元」。

    who -- "foreign"／"trust"／"dealer"（中文也收），只要某個身份別。
           institutional.foreign(date) 是 institutional(date, who="foreign") 的縮寫。
    """
    df = post_csv(_BASE + "totalTableDateDown", _dates(date))
    return _filter_who(df, who)


@who_shortcuts
def institutional_futures(date, who: str | None = None, product: str | None = None) -> pd.DataFrame:
    """三大法人—期貨契約（依商品分）：臺股期貨、小型臺指…逐商品列。

    注意金額單位是「千元」，跟總表的百萬元不一樣，期交所就是這樣給的。

    who     -- 同 institutional；institutional_futures.foreign(date) 也通
    product -- 用「商品名稱」篩，例如 "臺股期貨"
    """
    df = post_csv(_BASE + "futContractsDateDown", _dates(date))
    return _filter_eq(_filter_who(df, who), "商品名稱", product)


@who_shortcuts
def institutional_options(date, who: str | None = None, product: str | None = None,
                          side: str | None = None) -> pd.DataFrame:
    """三大法人—選擇權（買賣權分計）：CALL 與 PUT 分開列。金額單位「千元」。

    who     -- 同 institutional
    product -- 用「商品名稱」篩，例如 "臺指選擇權"
    side    -- "CALL" 或 "PUT"
    """
    df = post_csv(_BASE + "callsAndPutsDateDown", _dates(date))
    df = _filter_eq(_filter_who(df, who), "商品名稱", product)
    return _filter_eq(df, "買賣權別", side.upper() if side else None)


def _daily(url: str, commodity_id: str, date) -> pd.DataFrame:
    day = norm_date(date)
    return post_csv(url, {
        "down_type": "1",
        "commodity_id": commodity_id,
        "queryStartDate": day,
        "queryEndDate": day,
    })


def _dates(date) -> dict:
    # 三大法人各端點吃的日期參數名不完全一致，全都給最省事
    day = norm_date(date)
    return {"queryStartDate": day, "queryEndDate": day, "queryDate": day}
