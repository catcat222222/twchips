"""共用的下載與解析：各交易所的 CSV 長相不同，但清理邏輯是一樣的。"""
from __future__ import annotations

import datetime as dt
import io

import pandas as pd
import requests

from . import __version__

_HEADERS = {"User-Agent": f"twchips/{__version__}"}

# 就算長得像數字也保留文字的欄位（例如到期月份 "202608" 或週別 "202607F5"）
_TEXT_COLS = {
    "交易日期",
    "日期",
    "契約",
    "到期月份(週別)",
    "買賣權",
    "買賣權別",
    "交易時段",
    "身份別",
    "商品名稱",
    "是否因訊息面暫停交易",
}

_SESSION_MAP = {"regular": "一般", "after_hours": "盤後"}


def post_csv(url: str, data: dict) -> pd.DataFrame:
    resp = requests.post(url, data=data, headers=_HEADERS, timeout=30)
    resp.raise_for_status()
    return parse_big5_csv(resp.content)


def parse_big5_csv(raw: bytes) -> pd.DataFrame:
    text = raw.decode("cp950")  # 期交所給的是 Big5
    # index_col=False：期貨檔每行結尾多一個逗號，不加這個 pandas 會把第一欄當 index、欄位整排位移
    df = pd.read_csv(io.StringIO(text), dtype=str, index_col=False)
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


def norm_date(date) -> str:
    if isinstance(date, (dt.date, dt.datetime)):
        return date.strftime("%Y/%m/%d")
    return str(date).strip().replace("-", "/")


def filter_session(df: pd.DataFrame, session: str | None) -> pd.DataFrame:
    if session is None or df.empty:
        return df
    if session not in _SESSION_MAP:
        raise ValueError(f"session 要是 None、'regular' 或 'after_hours'，收到 {session!r}")
    return df[df["交易時段"] == _SESSION_MAP[session]].reset_index(drop=True)
