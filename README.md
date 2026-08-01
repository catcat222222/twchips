# twchips

台灣市場籌碼資料的 Python 小工具。不用註冊、不用 token，直接跟交易所官網要資料，回來就是 pandas DataFrame。

會做這個是因為我自己的盤後流程每天要看三大法人和結算價，找了一圈：能用的爬蟲大多停更很久，活著的數據服務又要註冊拿 token。這段程式每個看籌碼的人大概都自己重寫過一遍，乾脆抽出來變成套件。

期交所在 `twchips.taifex`，證交所在 `twchips.twse`。

## 安裝

還沒上 PyPI，先用 git 裝：

```
pip install git+https://github.com/catcat222222/twchips
```

## 期交所

```python
from twchips import taifex

# 三大法人總表：期貨＋選擇權合計的交易與未平倉（網站三大法人專區第一頁）
tot = taifex.institutional("2026-07-31")

# 只要某個身份別：.foreign／.trust／.dealer，或 who= 給中文也行
foreign = taifex.institutional.foreign("2026-07-31")

# 拆細：期貨依商品分、選擇權 CALL/PUT 分計，可以疊 who、product、side
txf = taifex.institutional_futures.foreign("2026-07-31", product="臺股期貨")
puts = taifex.institutional_options("2026-07-31", side="PUT")

# 日行情：台指期、台指選擇權整條鏈
fut = taifex.futures_daily("2026-07-31", session="regular")
opt = taifex.options_daily("2026-07-31", session="regular")
```

日行情的商品代號照期交所的來（`TX`、`MTX`、`TXO`⋯，完整清單看[期交所商品頁](https://www.taifex.com.tw/cht/2/tPEChain)）；三大法人 `product=` 吃的是中文「商品名稱」，當天有哪些直接看 `institutional_futures(date)["商品名稱"].unique()` 最準。`session` 給 `"regular"`（一般時段）、`"after_hours"`（盤後），不給就是全部。

## 證交所

```python
from twchips import twse

# 三大法人買賣金額統計（整體市場，單位：元）
tot = twse.institutional("2026-07-31")

# 個股三大法人買賣超（單位：股），stock= 只要一檔
tsmc = twse.institutional_stocks("2026-07-31", stock="2330")

# 融資融券：整體市場三列統計，或個股餘額
m = twse.margin("2026-07-31")
ms = twse.margin_stocks("2026-07-31", stock="2330")
```

證交所的身份別比期交所細：自營商拆「自行買賣／避險」、外資拆「外資及陸資／外資自營商」，所以 `twse.institutional.foreign(...)` 會回兩列——照原樣給，不幫你加總。

## 值的清理

欄位名稱保留交易所的原文中文，值有清過——千分位逗號、`-`、百分比符號都處理掉了，數字欄是真的數字，代號欄（像 `2330`）保持文字。非交易日會拿到空的 DataFrame，不會報錯。

幾個交易所自帶的陷阱，這裡都處理或至少告訴你：

- 期交所三大法人**總表的金額單位是百萬元、依商品分和選擇權分計是千元**。欄名裡有寫，運算前看一眼。
- 網站上的「合計」列期交所 CSV 沒有（要自己 `sum()`），證交所 JSON 有。
- 期貨日行情的 CSV 每行結尾多一個逗號，直接餵 pandas 欄位會整排位移——這包已經處理掉了。
- 證交所融資融券個股表的融資、融券欄名原始資料是撞名的，這裡已加前綴分開（`融資買進`、`融券買進`）。

## 已知限制

- 一次只能抓一天。要抓一段歷史請自己迴圈，中間記得 sleep——證交所對狂打的 IP 會直接封鎖，期交所也別欺負。
- 櫃買中心（上櫃股票的籌碼）還沒做。
- 期交所的每筆成交（tick）跟最後結算價也還沒做，做到我自己需要的時候會加。
- 交易所哪天改版面這個就會壞。測試用的是真實回應的存檔，發現壞了開 issue 跟我說。

## 關於 AI

程式碼是我跟 Claude Code 一起寫的。

## 免責

資料屬於臺灣期貨交易所（TAIFEX）與臺灣證券交易所（TWSE）。這個套件只是存取工具，內容不構成投資建議。
