# twchips

台灣市場籌碼資料的 Python 套件。不用註冊、不用 token，直接跟交易所官網要資料，回來是 pandas DataFrame。

期交所在 `twchips.taifex`，證交所在 `twchips.twse`。

## 安裝

還沒上 PyPI：

```
pip install git+https://github.com/catcat222222/twchips
```

## 用法

```python
from twchips import taifex

# 三大法人總表（期貨＋選擇權合計）
tot = taifex.institutional("2026-07-31")

# 只要某個身份別：.foreign／.trust／.dealer
foreign = taifex.institutional.foreign("2026-07-31")

# 期貨依商品分、選擇權 CALL/PUT 分計
txf = taifex.institutional_futures.foreign("2026-07-31", product="臺股期貨")
puts = taifex.institutional_options("2026-07-31", side="PUT")

# 日行情
fut = taifex.futures_daily("2026-07-31", session="regular")
opt = taifex.options_daily("2026-07-31", session="regular")
```

```python
from twchips import twse

tot = twse.institutional("2026-07-31")                     # 三大法人買賣金額
tsmc = twse.institutional_stocks("2026-07-31", stock="2330")  # 個股三大法人買賣超
m = twse.margin("2026-07-31")                              # 融資融券統計
ms = twse.margin_stocks("2026-07-31", stock="2330")        # 個股融資融券
```

商品代號照期交所（`TX`、`MTX`、`TXO`⋯）。三大法人的 `product=` 吃中文商品名稱，有哪些看 `["商品名稱"].unique()`。`session`：`"regular"`、`"after_hours"`，不給就是全部。

欄位名稱保留交易所原文。數字欄已轉數字（千分位、`-`、`%` 都清掉），代號欄保持文字。非交易日回空的 DataFrame。

## 注意

- 期交所三大法人的金額單位：總表是百萬元，依商品分和選擇權分計是千元。
- 「合計」列期交所 CSV 沒有，證交所 JSON 有。
- 證交所個股融資融券的同名欄位已加前綴（`融資買進`、`融券買進`）。
- 證交所的身份別較細（自營商×2、外資×2），`foreign` 會回兩列，不幫你加總。
- 抓歷史請迴圈加 sleep，證交所會封鎖狂打的 IP。

## 還沒做

- 日期區間（一次只能抓一天）
- 櫃買中心
- tick、最後結算價

交易所改版面就會壞，壞了開 issue。

## 關於 AI

程式碼是我跟 Claude Code 一起寫的。

## 免責

資料屬於 TAIFEX 與 TWSE。非投資建議。
