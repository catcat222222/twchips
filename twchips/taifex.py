"""期交所（TAIFEX）：日行情與三大法人。"""
from __future__ import annotations

import pandas as pd

from ._core import filter_session, norm_date, post_csv

_BASE = "https://www.taifex.com.tw/cht/3/"


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


def institutional(date) -> pd.DataFrame:
    """三大法人「總表」：期貨＋選擇權合計的交易與未平倉，多空口數與契約金額。

    就是期交所網站三大法人專區第一頁那兩張表，攤平成一張。
    身份別：自營商、投信、外資及陸資。金額單位是「百萬元」。
    """
    return post_csv(_BASE + "totalTableDateDown", _dates(date))


def institutional_futures(date) -> pd.DataFrame:
    """三大法人—期貨契約（依商品分）：臺股期貨、小型臺指…逐商品列。

    注意金額單位是「千元」，跟總表的百萬元不一樣，期交所就是這樣給的。
    """
    return post_csv(_BASE + "futContractsDateDown", _dates(date))


def institutional_options(date) -> pd.DataFrame:
    """三大法人—選擇權（買賣權分計）：CALL 與 PUT 分開列。金額單位「千元」。"""
    return post_csv(_BASE + "callsAndPutsDateDown", _dates(date))


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
