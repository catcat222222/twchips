"""抓台灣期交所（TAIFEX）每日行情的小工具。

直接打期交所官網的下載端點，不需要帳號、不需要 token。
資料屬於期交所，請溫柔使用。
"""
from __future__ import annotations

import datetime as dt
import io

import pandas as pd
import requests

__version__ = "0.1.0"

_FUT_URL = "https://www.taifex.com.tw/cht/3/futDataDown"
_OPT_URL = "https://www.taifex.com.tw/cht/3/optDataDown"
_HEADERS = {"User-Agent": f"taifex-daily/{__version__}"}

# 這些欄位就算長得像數字也保留文字（例如到期月份 "202608" 或週別 "202607F5"）
_TEXT_COLS = {
    "交易日期",
    "契約",
    "到期月份(週別)",
    "買賣權",
    "交易時段",
    "是否因訊息面暫停交易",
}

_SESSION_MAP = {"regular": "一般", "after_hours": "盤後"}


def futures_daily(date, product: str = "TX", session: str | None = None) -> pd.DataFrame:
    """抓某一天的期貨日行情（開高低收、結算價、未沖銷契約數…）。

    date     -- "2026-07-31"、"2026/07/31" 或 datetime.date 都可以
    product  -- 商品代號，預設 TX（台指期）；MTX、TE、TF… 也通
    session  -- None＝全部；"regular"＝一般時段；"after_hours"＝盤後時段
    """
    df = _download(_FUT_URL, product, date)
    return _filter_session(df, session)


def options_daily(date, product: str = "TXO", session: str | None = None) -> pd.DataFrame:
    """抓某一天的選擇權日行情（整條鏈：履約價、買賣權、結算價…）。

    參數同 futures_daily，product 預設 TXO（台指選擇權）。
    """
    df = _download(_OPT_URL, product, date)
    return _filter_session(df, session)


def _download(url: str, commodity_id: str, date) -> pd.DataFrame:
    day = _norm_date(date)
    resp = requests.post(
        url,
        data={
            "down_type": "1",
            "commodity_id": commodity_id,
            "queryStartDate": day,
            "queryEndDate": day,
        },
        headers=_HEADERS,
        timeout=30,
    )
    resp.raise_for_status()
    return _parse(resp.content)


def _parse(raw: bytes) -> pd.DataFrame:
    text = raw.decode("cp950")  # 期交所給的是 Big5
    # index_col=False：期貨檔每行結尾多一個逗號，不加這個 pandas 會把第一欄當 index、欄位整排位移
    df = pd.read_csv(io.StringIO(text), dtype=str, index_col=False)
    # 行尾多一個逗號會生出一欄 Unnamed，砍掉
    df = df.loc[:, [not c.startswith("Unnamed") for c in df.columns]]
    df.columns = [c.strip() for c in df.columns]
    if df.empty:
        return df  # 非交易日：只有表頭
    df = df.apply(lambda s: s.str.strip())
    for col in df.columns:
        if col not in _TEXT_COLS:
            df[col] = _maybe_numeric(df[col])
        else:
            df[col] = df[col].replace({"-": pd.NA, "": pd.NA})
    return df


def _maybe_numeric(s: pd.Series) -> pd.Series:
    """整欄轉數字；轉不動的欄位（未知的文字欄）原樣保留，只把 '-' 換成 NA。"""
    cleaned = s.str.replace(",", "", regex=False).str.rstrip("%")
    cleaned = cleaned.replace({"-": None, "": None})
    num = pd.to_numeric(cleaned, errors="coerce")
    if (num.isna() & cleaned.notna()).any():
        return s.replace({"-": pd.NA, "": pd.NA})
    return num


def _norm_date(date) -> str:
    if isinstance(date, (dt.date, dt.datetime)):
        return date.strftime("%Y/%m/%d")
    return str(date).strip().replace("-", "/")


def _filter_session(df: pd.DataFrame, session: str | None) -> pd.DataFrame:
    if session is None or df.empty:
        return df
    if session not in _SESSION_MAP:
        raise ValueError(f"session 要是 None、'regular' 或 'after_hours'，收到 {session!r}")
    return df[df["交易時段"] == _SESSION_MAP[session]].reset_index(drop=True)
