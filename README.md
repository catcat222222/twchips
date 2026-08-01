# twchips

台灣市場籌碼資料的 Python 小工具。不用註冊、不用 token，直接跟交易所官網要資料，回來就是 pandas DataFrame。

會做這個是因為我自己的盤後流程每天要看三大法人和結算價，找了一圈：能用的爬蟲大多停更很久，活著的數據服務又要註冊拿 token。這段程式每個看籌碼的人大概都自己重寫過一遍，乾脆抽出來變成套件。

目前只有期交所（`twchips.taifex`）。證交所的部分在路上，所以名字取大了一點。

## 安裝

還沒上 PyPI，先用 git 裝：

```
pip install git+https://github.com/catcat222222/twchips
```

## 用法

```python
from twchips import taifex

# 三大法人總表：期貨＋選擇權合計的交易與未平倉（就是網站三大法人專區第一頁）
tot = taifex.institutional("2026-07-31")

# 三大法人拆細：期貨依商品分、選擇權 CALL/PUT 分計
fut_inst = taifex.institutional_futures("2026-07-31")
txf = fut_inst[fut_inst["商品名稱"] == "臺股期貨"]
opt_inst = taifex.institutional_options("2026-07-31")

# 日行情：台指期、台指選擇權整條鏈
fut = taifex.futures_daily("2026-07-31", session="regular")
opt = taifex.options_daily("2026-07-31", session="regular")
```

商品代號照期交所的來：`TX`、`MTX`、`TE`、`TF`、`TXO`⋯⋯。`session` 給 `"regular"`（一般時段）、`"after_hours"`（盤後），不給就是全部。

欄位名稱保留交易所的原文中文，值有清過——千分位逗號、`-`、百分比符號都處理掉了，數字欄是真的數字。非交易日會拿到空的 DataFrame，不會報錯。

幾個期交所自帶的陷阱，這裡都處理或至少告訴你：

- 三大法人**總表的金額單位是百萬元、依商品分和選擇權分計是千元**。欄名裡有寫，運算前看一眼。
- 網站上的「合計」列 CSV 版沒有，要合計自己 `sum()`。
- 期貨日行情的 CSV 每行結尾多一個逗號，直接餵 pandas 欄位會整排位移——這包已經處理掉了。

## 已知限制

- 一次只能抓一天。要抓一段歷史請自己迴圈，中間記得 sleep——資料是交易所免費提供的，別把人家打掛。
- 證交所（個股三大法人買賣超、融資融券那些）還沒做，這是下一步。
- 每筆成交（tick）跟最後結算價也還沒做，做到我自己需要的時候會加。
- 交易所哪天改版面這個就會壞。測試用的是真實回應的存檔，發現壞了開 issue 跟我說。

## 關於 AI

程式碼是我跟 Claude Code 一起寫的。要抓什麼、介面長怎樣、哪些先不做，是我決定的。

## 免責

資料屬於臺灣期貨交易所（TAIFEX）與臺灣證券交易所（TWSE）。這個套件只是存取工具，內容不構成投資建議。
