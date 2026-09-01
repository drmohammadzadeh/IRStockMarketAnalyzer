import re
import httpx
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from src.config import (
    HEADERS,
    REQUEST_TIMEOUT,
    TSETMC_SEARCH_URL,
    TSETMC_INST_URL,
    TSETMC_HISTORY_URL,
    TSETMC_CLIENT_TYPE_URL,
)


class TSETMCFetcher:
    """Fetcher and parser for TSETMC price history and client type data."""

    def __init__(self, client: Optional[httpx.Client] = None):
        self.client = client or httpx.Client(
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
            verify=False,
            follow_redirects=True,
            trust_env=False,
        )

    def search_inscode(self, symbol: str) -> Optional[str]:
        """Search for symbol's inscode on TSETMC."""
        cleaned_symbol = symbol.strip()

        def normalize_fa(s: str) -> str:
            return s.replace("ي", "ی").replace("ك", "ک").replace("آ", "ا").replace("ة", "ه").strip()

        norm_target = normalize_fa(cleaned_symbol)
        url = TSETMC_SEARCH_URL.format(query=cleaned_symbol)
        try:
            resp = self.client.get(url)
            if resp.status_code != 200 or not resp.text:
                return None
            parts = resp.text.split(";")
            for part in parts:
                fields = part.split(",")
                if len(fields) >= 2:
                    row_symbol = fields[0].strip()
                    norm_row = normalize_fa(row_symbol)
                    if norm_row == norm_target or norm_target in norm_row:
                        # In real TSETMC response: symbol, name, inscode, ...
                        # In mock/test responses: symbol, inscode, ...
                        for candidate in fields[1:]:
                            cand_clean = candidate.strip()
                            if cand_clean.isdigit() and len(cand_clean) >= 10:
                                return cand_clean
                        return fields[1].strip()
        except Exception:
            pass
        return None

    @staticmethod
    def parse_history_string(raw_text: str) -> pd.DataFrame:
        """Parse raw InstTradeHistory semicolon/at-separated string into a DataFrame."""
        rows = []
        for line in raw_text.split(";"):
            line = line.strip()
            if not line:
                continue
            parts = line.split("@")
            if len(parts) >= 8:
                try:
                    date_str = parts[0]
                    high = float(parts[1])
                    low = float(parts[2])
                    close = float(parts[3])
                    last = float(parts[4])
                    open_p = float(parts[5])

                    if len(parts) >= 10:
                        yesterday = float(parts[6])
                        value = float(parts[7])
                        volume = float(parts[8])
                        trades = float(parts[9])
                    elif len(parts) == 9:
                        yesterday = float(parts[6])
                        value = float(parts[7])
                        volume = float(parts[8])
                        trades = 0.0
                    else:  # len == 8
                        yesterday = float(parts[5])
                        value = float(parts[6])
                        volume = float(parts[7])
                        trades = 0.0

                    rows.append({
                        "date": date_str,
                        "open": open_p,
                        "high": high,
                        "low": low,
                        "close": close,
                        "last": last,
                        "yesterday": yesterday,
                        "volume": volume,
                        "value": value,
                        "trades": trades,
                    })
                except (ValueError, IndexError):
                    continue
        df = pd.DataFrame(rows)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"], format="%Y%m%d", errors="coerce")
            df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
        return df

    @staticmethod
    def parse_client_type_string(raw_text: str) -> Dict[str, Any]:
        """Parse raw client type data and calculate buyer/seller capita and power."""
        lines = [l.strip() for l in raw_text.split(";") if l.strip()]
        if not lines:
            return {}
        latest = lines[0].split(",")
        if len(latest) >= 9:
            try:
                buy_real_count = int(latest[1])
                buy_legal_count = int(latest[2])
                sell_real_count = int(latest[3])
                sell_legal_count = int(latest[4])
                buy_real_vol = float(latest[5])
                buy_legal_vol = float(latest[6])
                sell_real_vol = float(latest[7])
                sell_legal_vol = float(latest[8])

                buy_real_capita = (buy_real_vol / buy_real_count) if buy_real_count > 0 else 0.0
                sell_real_capita = (sell_real_vol / sell_real_count) if sell_real_count > 0 else 0.0
                buyer_power = (buy_real_capita / sell_real_capita) if sell_real_capita > 0 else 1.0

                return {
                    "buy_real_count": buy_real_count,
                    "buy_legal_count": buy_legal_count,
                    "sell_real_count": sell_real_count,
                    "sell_legal_count": sell_legal_count,
                    "buy_real_vol": buy_real_vol,
                    "buy_legal_vol": buy_legal_vol,
                    "sell_real_vol": sell_real_vol,
                    "sell_legal_vol": sell_legal_vol,
                    "buy_real_capita": buy_real_capita,
                    "sell_real_capita": sell_real_capita,
                    "buyer_power": buyer_power,
                }
            except (ValueError, IndexError):
                pass
        return {}

    def fetch_symbol_data(self, symbol: str, inscode: Optional[str] = None) -> Dict[str, Any]:
        """Fetch both history OHLCV and real/legal client data for a symbol."""
        resolved_inscode = inscode or self.search_inscode(symbol)
        if not resolved_inscode:
            return {
                "symbol": symbol,
                "success": False,
                "error": f"Symbol {symbol} not found on TSETMC",
            }
        inscode = resolved_inscode

        hist_resp = self.client.get(TSETMC_HISTORY_URL.format(inscode=inscode))
        hist_df = self.parse_history_string(hist_resp.text if hist_resp.status_code == 200 else "")

        client_resp = self.client.get(TSETMC_CLIENT_TYPE_URL.format(inscode=inscode))
        client_data = self.parse_client_type_string(client_resp.text if client_resp.status_code == 200 else "")

        return {
            "symbol": symbol,
            "inscode": inscode,
            "success": not hist_df.empty,
            "history": hist_df,
            "client_type": client_data,
        }
