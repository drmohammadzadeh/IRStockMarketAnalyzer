import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STOCKS_DIR = BASE_DIR / "سهام"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

TSETMC_SEARCH_URL = "http://old.tsetmc.com/tsev2/data/search.aspx?skey={query}"
TSETMC_INST_URL = "http://old.tsetmc.com/Loader.aspx?ParTree=151311&i={inscode}"
TSETMC_HISTORY_URL = "http://old.tsetmc.com/tsev2/data/InstTradeHistory.aspx?i={inscode}&Top=999999&A=0"
TSETMC_CLIENT_TYPE_URL = "http://old.tsetmc.com/tsev2/data/clienttype.aspx?i={inscode}"
CODAL_SEARCH_API = "https://search.codal.ir/api/search/v2/q"

REQUEST_TIMEOUT = 15
MAX_RETRIES = 3
