"""打真站的 schema 哨兵：每個交易日收盤後真的去問一次交易所。

跟另外三支離線測試的分工：
  test_parse / test_institutional / test_twse  吃 tests/data 裡 2026-07-31 錄下來的樣本，
      驗的是「解析邏輯有沒有被自己改壞」。樣本是死的，官網改版它一輩子不會知道。
  本檔                                          驗的是「官網有沒有變」。

爬官網的套件最貴的故障不是報錯，是不報錯——交易所多插一欄、改個欄名、把數字欄
變成帶註記的文字，解析照樣回一張長得很正常的表，錯位的數字要好幾天才會被發現。
所以這裡的比對基準就是離線測試用的那批樣本：**今天真站回來的欄位，必須跟當初錄樣本時
一字不差**，順序也算。多一欄、少一欄、改個名，紅燈。

另外驗幾條「數字之間該成立的關係」（淨額＝多方－空方、合計＝各分項相加、
融資餘額＝前日＋買進－賣出－償還），這種在欄位錯位時會第一個爆掉。

預設不跑：要連外網，非交易日、交易所維護都會製造噪音，不該綁在每次 commit 上。
CI 排程與手動才開：

    TWCHIPS_LIVE=1 pytest tests/test_live.py -q
"""
from __future__ import annotations

import datetime as dt
import json
import os
import time
from pathlib import Path

import pandas as pd
import pytest

from twchips import taifex, twse
from twchips._core import json_table, parse_big5_csv

pytestmark = pytest.mark.skipif(
    os.environ.get("TWCHIPS_LIVE") != "1",
    reason="要打真站的測試，設 TWCHIPS_LIVE=1 才跑",
)

DATA = Path(__file__).parent / "data"

# 往回找最近一個有資料的交易日：連假最長大概 5 個工作天（春節），抓寬一點
MAX_LOOKBACK_DAYS = 12
# 證交所對狂打的 IP 會直接封鎖，每次請求之間留一點空隙
PACE_SECONDS = 1.5


def _pace() -> None:
    time.sleep(PACE_SECONDS)


def _csv_columns(name: str) -> list[str]:
    """當初錄樣本時的欄位（期交所 Big5 CSV）。"""
    return list(parse_big5_csv((DATA / name).read_bytes()).columns)


def _json_columns(name: str, table: int | None = None) -> list[str]:
    """當初錄樣本時的欄位（證交所 JSON）。"""
    payload = json.load(open(DATA / name, encoding="utf-8"))
    if table is not None:
        payload = payload["tables"][table]
    return list(json_table(payload).columns)


def _walk_back(fetch, label: str):
    """從今天往回找第一個抓得到資料的日子，回 (日期, DataFrame)。

    找不到就 fail，不 skip——連續十幾天抓不到東西本身就是要知道的事。
    """
    today = dt.date.today()
    errors = []
    for back in range(MAX_LOOKBACK_DAYS):
        day = today - dt.timedelta(days=back)
        if day.weekday() >= 5:  # 週末不用問
            continue
        try:
            df = fetch(day)
        except Exception as exc:  # 連線被擋、逾時
            errors.append(f"{day}: {type(exc).__name__} {exc}")
            _pace()
            continue
        if not df.empty:
            return day, df
        _pace()
    raise AssertionError(
        f"{label}：往回 {MAX_LOOKBACK_DAYS} 天都拿不到資料。"
        f"可能是交易所改版、端點搬家，或 CI 的 IP 被擋。"
        + (f"\n途中的錯誤：\n" + "\n".join(errors) if errors else "")
    )


# ---------------------------------------------------------------- 期交所


@pytest.fixture(scope="module")
def fut():
    day, df = _walk_back(lambda d: taifex.futures_daily(d, "TX"), "期交所日行情 TX")
    print(f"\n[live] 期交所交易日 = {day}")
    return df


@pytest.fixture(scope="module")
def fut_day(fut):
    return str(fut.iloc[0]["交易日期"]).replace("/", "-")


def test_futures_daily_schema(fut):
    assert list(fut.columns) == _csv_columns("fut_20260731.csv")


def test_futures_daily_sane(fut):
    assert set(fut["交易時段"]) <= {"一般", "盤後"}
    assert (fut["契約"] == "TX").all()
    assert pd.api.types.is_numeric_dtype(fut["收盤價"])
    assert not pd.api.types.is_numeric_dtype(fut["到期月份(週別)"])  # 202608 不能變數字
    traded = fut[fut["成交量"] > 0]
    assert not traded.empty
    assert (traded["最高價"] >= traded["最低價"]).all()
    assert (traded["收盤價"] > 0).all()
    # 盤後時段這欄是 "-"（→ NA），只驗有值的那些
    assert (traded["未沖銷契約數"].dropna() >= 0).all()
    assert traded["未沖銷契約數"].notna().any()


def test_options_daily_schema(fut_day):
    _pace()
    opt = taifex.options_daily(fut_day, "TXO")
    assert not opt.empty
    assert list(opt.columns) == _csv_columns("opt_20260731_head.csv")
    assert set(opt["買賣權"]) <= {"買權", "賣權"}
    assert pd.api.types.is_numeric_dtype(opt["履約價"])
    assert (opt["履約價"] > 0).all()


def test_institutional_total_schema(fut_day):
    _pace()
    df = taifex.institutional(fut_day)
    assert not df.empty
    assert list(df.columns) == _csv_columns("institutional_total_20260731.csv")
    assert set(df["身份別"]) == {"自營商", "投信", "外資及陸資"}
    # 淨額欄跟多空欄要對得起來，欄位錯位時這裡第一個爆
    assert (df["多空交易口數淨額"] == df["多方交易口數"] - df["空方交易口數"]).all()
    assert (df["多空未平倉口數淨額"] == df["多方未平倉口數"] - df["空方未平倉口數"]).all()


def test_institutional_futures_schema(fut_day):
    _pace()
    df = taifex.institutional_futures(fut_day)
    assert not df.empty
    assert list(df.columns) == _csv_columns("institutional_fut_20260731.csv")
    assert "臺股期貨" in set(df["商品名稱"])
    assert (df["多空交易口數淨額"] == df["多方交易口數"] - df["空方交易口數"]).all()
    # 依商品的金額單位是千元，跟總表的百萬元不能混
    assert "多方交易契約金額(千元)" in df.columns


def test_institutional_options_schema(fut_day):
    _pace()
    df = taifex.institutional_options(fut_day)
    assert not df.empty
    assert list(df.columns) == _csv_columns("institutional_opt_20260731.csv")
    assert set(df["買賣權別"]) == {"CALL", "PUT"}
    assert (df["交易口數買賣淨額"] == df["買方交易口數"] - df["賣方交易口數"]).all()


def test_who_filter_still_matches_live_labels(fut_day):
    """期交所哪天把「外資及陸資」改個名，who="foreign" 會靜靜回空表——這裡要抓到。"""
    _pace()
    df = taifex.institutional.foreign(fut_day)
    assert len(df) == 1
    assert df.iloc[0]["身份別"] == "外資及陸資"


# ---------------------------------------------------------------- 證交所


@pytest.fixture(scope="module")
def twse_pair():
    day, df = _walk_back(twse.institutional, "證交所三大法人 BFI82U")
    print(f"[live] 證交所交易日 = {day}")
    return day, df


def test_twse_institutional_schema(twse_pair):
    _, df = twse_pair
    assert list(df.columns) == _json_columns("twse_bfi82u_20260731.json")
    assert set(df["單位名稱"]) == {
        "自營商(自行買賣)", "自營商(避險)", "投信",
        "外資及陸資(不含外資自營商)", "外資自營商", "合計",
    }
    assert (df["買賣差額"] == df["買進金額"] - df["賣出金額"]).all()
    total = df[df["單位名稱"] == "合計"].iloc[0]
    parts = df[df["單位名稱"] != "合計"]
    assert total["買賣差額"] == parts["買賣差額"].sum()


def test_twse_who_filter_still_matches_live_labels(twse_pair):
    day, _ = twse_pair
    _pace()
    df = twse.institutional.foreign(day)
    assert len(df) == 2  # 外資及陸資(不含外資自營商)、外資自營商
    assert df["單位名稱"].str.startswith("外資").all()


def test_twse_institutional_stocks_schema(twse_pair):
    day, _ = twse_pair
    _pace()
    df = twse.institutional_stocks(day)
    assert not df.empty
    assert list(df.columns) == _json_columns("twse_t86_20260731.json")
    assert not pd.api.types.is_numeric_dtype(df["證券代號"])  # 2330 是代號不是數字
    assert "2330" in set(df["證券代號"])
    # 三大法人合計＝外陸資＋外資自營商＋投信＋自營商
    parts = (df["外陸資買賣超股數(不含外資自營商)"] + df["外資自營商買賣超股數"]
             + df["投信買賣超股數"] + df["自營商買賣超股數"])
    assert (df["三大法人買賣超股數"] == parts).all()
    # 自營商＝自行買賣＋避險
    assert (df["自營商買賣超股數"]
            == df["自營商買賣超股數(自行買賣)"] + df["自營商買賣超股數(避險)"]).all()


def test_twse_margin_schema(twse_pair):
    day, _ = twse_pair
    _pace()
    df = twse.margin(day)
    assert list(df.columns) == _json_columns("twse_margn_20260731.json", table=0)
    assert list(df["項目"]) == ["融資(交易單位)", "融券(交易單位)", "融資金額(仟元)"]
    # 融資：買進是開倉，餘額增加；融券反過來，賣出才是開倉。
    # 這兩條方向不同，錯位或欄位對調時剛好一起爆。
    long_rows = df[df["項目"] != "融券(交易單位)"]
    assert (long_rows["今日餘額"]
            == long_rows["前日餘額"] + long_rows["買進"] - long_rows["賣出"]
            - long_rows["現金(券)償還"]).all()
    short_row = df[df["項目"] == "融券(交易單位)"].iloc[0]
    assert (short_row["今日餘額"]
            == short_row["前日餘額"] + short_row["賣出"] - short_row["買進"]
            - short_row["現金(券)償還"])


def test_twse_margin_stocks_schema(twse_pair):
    day, _ = twse_pair
    _pace()
    df = twse.margin_stocks(day)
    assert not df.empty
    assert list(df.columns) == _json_columns("twse_margn_20260731.json", table=1)
    assert len(df.columns) == len(set(df.columns))  # groups 前綴沒加好會撞名
    assert "2330" in set(df["代號"])
    assert (df["融資今日餘額"]
            == df["融資前日餘額"] + df["融資買進"] - df["融資賣出"]
            - df["融資現金償還"]).all()
