"""台灣市場籌碼資料的小工具。

直接打交易所官網的公開端點，不需要帳號、不需要 token。
目前有期交所（twchips.taifex）；證交所（twchips.twse）在路上。
資料屬於各交易所，請溫柔使用。
"""

__version__ = "0.1.0"

from . import taifex  # noqa: E402,F401
