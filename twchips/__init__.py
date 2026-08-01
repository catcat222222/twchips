"""台灣市場籌碼資料的小工具。

直接打交易所官網的公開端點，不需要帳號、不需要 token。
期交所在 twchips.taifex，證交所在 twchips.twse。
資料屬於各交易所，請溫柔使用。
"""

__version__ = "0.1.0"

from . import taifex, twse  # noqa: E402,F401
