"""Frontend Agent for Iranian Stock Market Analyzer.

Author: alimohammadzadeh@ut.ac.ir
Role: Scans stock directories under سهام/, extracts real trading metrics,
14-day history, and reports, and normalizes them into JSON database stocks.json.
"""

import csv
import datetime
import json
import math
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import jdatetime

from src.config import STOCKS_DIR

PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")

STOCK_NAMES: Dict[str, str] = {
    "تابان": "گروه پتروشیمی تابان فردا",
    "کلید": "صندوق املاک و مستغلات کلید",
    "وتجارت": "بانک تجارت",
    "تلیسه": "دامداری تلیسه نمونه",
    "خودرو": "ایران خودرو",
    "زهلال": "کشت و صنعت و دامپروری صنایع غذایی هلال (کشت و صنعت هلال)",
    "فسازان": "غلتک‌سازان سپاهان",
    "بانیان": "نيان باتري خاوران",
}


def to_persian_digits(val: Union[int, str]) -> str:
    """Convert English digits to Persian digits."""
    return str(val).translate(PERSIAN_DIGITS)


def format_persian_date(iso_date_str: str) -> str:
    """Convert ISO date string (YYYY-MM-DD) to Persian date (e.g. '۶ مرداد')."""
    try:
        dt = datetime.date.fromisoformat(iso_date_str.strip())
        jdt = jdatetime.date.fromgregorian(date=dt)
        month_name = jdt.j_months_fa[jdt.month - 1]
        day_str = to_persian_digits(jdt.day)
        return f"{day_str} {month_name}"
    except Exception:
        return iso_date_str


def format_volume(vol: Optional[Union[float, int, str]]) -> str:
    """Format trading volume with M/B/K suffixes."""
    if vol is None:
        return "—"
    try:
        v = float(vol)
        if math.isnan(v) or v <= 0:
            return "—"
        if v >= 1_000_000_000:
            return f"{v / 1_000_000_000:.1f}B"
        elif v >= 1_000_000:
            return f"{v / 1_000_000:.1f}M"
        elif v >= 1_000:
            return f"{v / 1_000:.1f}K"
        else:
            return f"{v:,.0f}"
    except Exception:
        return "—"


class FrontendAgent:
    """Discovers stock folders, normalizes metrics, and synchronizes the frontend database."""

    def __init__(
        self,
        stocks_dir: Optional[Union[str, Path]] = None,
        browser_dir: Optional[Union[str, Path]] = None,
    ) -> None:
        self.stocks_dir = Path(stocks_dir or STOCKS_DIR)
        self.browser_dir = Path(
            browser_dir or (self.stocks_dir.parent / "browser")
        )

    def _extract_market_cap(self, symbol_dir: Path) -> str:
        """Extract market cap from fundamental report if available."""
        fund_file = symbol_dir / "fundamental_report.md"
        if not fund_file.exists():
            return "—"
        try:
            content = fund_file.read_text(encoding="utf-8")
            match = re.search(
                r"\*\*ارزش بازار:\*\*\s*\*\*([^*]+)\*\*(?:\s*\(([\d,]+)\s*ریال\))?",
                content,
            )
            if match:
                if match.group(2):
                    rial_num = int(match.group(2).replace(",", ""))
                    return f"{rial_num // 1_000_000_000:,} B"
                cap_text = match.group(1).strip()
                return cap_text if cap_text else "—"
        except Exception:
            pass
        return "—"

    def _extract_links(self, symbol: str, symbol_dir: Path) -> Dict[str, str]:
        """Extract official and github links for the given symbol."""
        links_file = symbol_dir / "links.txt"
        tsetmc_url = f"https://old.tsetmc.com/tsev2/data/search.aspx?skey={symbol}"
        rahavard_url = f"https://rahavard365.com/asset/search?q={symbol}"
        codal_url = f"https://codal.ir/ReportList.aspx?search&Symbol={symbol}"

        if links_file.exists():
            try:
                for line in links_file.read_text(encoding="utf-8").splitlines():
                    clean_line = line.strip()
                    if not clean_line.startswith("http"):
                        continue
                    if "tsetmc" in clean_line.lower():
                        tsetmc_url = clean_line
                    elif "rahavard" in clean_line.lower():
                        rahavard_url = clean_line
                    elif "codal" in clean_line.lower():
                        codal_url = clean_line
            except Exception:
                pass

        return {
            "tsetmc": tsetmc_url,
            "rahavard": rahavard_url,
            "codal": codal_url,
            "technical_github": f"https://github.com/drmohammadzadeh/IRStockMarketAnalyzer/blob/main/سهام/{symbol}/technical_report.md",
            "fundamental_github": f"https://github.com/drmohammadzadeh/IRStockMarketAnalyzer/blob/main/سهام/{symbol}/fundamental_report.md",
            "readme_github": f"https://github.com/drmohammadzadeh/IRStockMarketAnalyzer/blob/main/سهام/{symbol}/README.md",
        }

    def _extract_stock(self, symbol_dir: Path) -> Optional[Dict[str, Any]]:
        """Extract all metrics and history for a single stock directory."""
        symbol = symbol_dir.name
        name = STOCK_NAMES.get(symbol, None)
        if not name:
            readme_path = symbol_dir / "README.md"
            if readme_path.exists():
                try:
                    for line in readme_path.read_text(encoding="utf-8").splitlines():
                        if "نام شرکت / دارایی" in line and "|" in line:
                            parts = [p.strip() for p in line.split("|")]
                            if len(parts) >= 3 and parts[2]:
                                ext_name = parts[2].replace("**", "").strip()
                                if ext_name and len(ext_name) > 1:
                                    name = ext_name
                                    break
                except Exception:
                    pass
        if not name:
            name = symbol

        # 1. Trade history and 14d chart
        csv_path = symbol_dir / "market_data" / "trade_history.csv"
        rows: List[Dict[str, Any]] = []
        if csv_path.exists():
            try:
                with open(csv_path, mode="r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if "date" in row and row["date"]:
                            rows.append(row)
            except Exception:
                pass

        chart_14d: List[Dict[str, Any]] = []
        current_price = 0.0
        change_percent = 0.0
        volume_formatted = "—"

        if rows:
            # Sort chronologically by date
            rows.sort(key=lambda r: r.get("date", ""))
            latest_14 = rows[-14:]

            for r in latest_14:
                try:
                    p = float(r.get("close", 0))
                    d = format_persian_date(r.get("date", ""))
                    chart_14d.append({"date": d, "price": p})
                except Exception:
                    continue

            latest_row = rows[-1]
            try:
                current_price = float(latest_row.get("close", 0.0))
            except Exception:
                current_price = 0.0

            try:
                vol_val = float(latest_row.get("volume", 0.0))
                volume_formatted = format_volume(vol_val)
            except Exception:
                volume_formatted = "—"

            try:
                yesterday = float(latest_row.get("yesterday", 0.0))
                if yesterday > 0:
                    change_percent = round(
                        ((current_price - yesterday) / yesterday) * 100, 2
                    )
                elif len(rows) >= 2:
                    prev_close = float(rows[-2].get("close", 0.0))
                    if prev_close > 0:
                        change_percent = round(
                            ((current_price - prev_close) / prev_close) * 100,
                            2,
                        )
            except Exception:
                change_percent = 0.0

        # 2. Strategy recommendation
        strat_path = symbol_dir / "strategy_recommendation.json"
        verdict = "—"
        score = None
        if strat_path.exists():
            try:
                strat_data = json.loads(strat_path.read_text(encoding="utf-8"))
                plan = strat_data.get("plan", {})
                if "current_price" in plan and plan["current_price"]:
                    current_price = float(plan["current_price"])
                verdict = strat_data.get("verdict") or plan.get(
                    "overall_verdict", "—"
                )
                score = plan.get("score")
            except Exception:
                pass

        # 3. Market cap and links
        market_cap_formatted = self._extract_market_cap(symbol_dir)
        links = self._extract_links(symbol, symbol_dir)

        return {
            "symbol": symbol,
            "name": name,
            "logo": "",
            "current_price": current_price,
            "change_percent": change_percent,
            "volume": volume_formatted,
            "market_cap": market_cap_formatted,
            "chart_14d": chart_14d,
            "links": links,
            "verdict": verdict,
            "score": score,
        }

    def scan_and_extract(self) -> List[Dict[str, Any]]:
        """Scans all subfolders in stocks_dir, extracts trading and report data."""
        if not self.stocks_dir.exists():
            return []

        stocks: List[Dict[str, Any]] = []
        for entry in sorted(self.stocks_dir.iterdir()):
            if entry.is_dir() and not entry.name.startswith((".", "_")):
                stock_data = self._extract_stock(entry)
                if stock_data:
                    stocks.append(stock_data)

        return stocks

    def generate_stocks_json(
        self, stocks_data: Optional[List[Dict[str, Any]]] = None
    ) -> Path:
        """Writes browser/data/stocks.json and stocks_dir/index.json atomically."""
        if stocks_data is None:
            stocks_data = self.scan_and_extract()

        # Write browser/data/stocks.json
        out_dir = self.browser_dir / "data"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "stocks.json"
        json_content = json.dumps(stocks_data, ensure_ascii=False, indent=2)
        out_file.write_text(json_content, encoding="utf-8")

        # Also write browser/data/stocks.js to allow opening index.html directly via file:// without CORS restrictions
        js_file = out_dir / "stocks.js"
        js_file.write_text(
            f"/**\n * Iranian Stock Market Watchlist Data Store\n * Auto-generated by FrontendAgent (alimohammadzadeh@ut.ac.ir)\n */\nwindow.STOCKS_DATA = {json_content};\n",
            encoding="utf-8",
        )

        # Also write stocks_dir/index.json
        if self.stocks_dir.exists():
            index_file = self.stocks_dir / "index.json"
            index_file.write_text(json_content, encoding="utf-8")

        return out_file

    def update_single_stock(self, symbol: str) -> Dict[str, Any]:
        """Extracts metrics for a single symbol and performs an atomic in-place upsert
        into browser/data/stocks.json, browser/data/stocks.js, and stocks_dir/index.json.
        """
        symbol_clean = symbol.strip()
        symbol_dir = self.stocks_dir / symbol_clean
        if not symbol_dir.exists():
            raise FileNotFoundError(f"Symbol directory not found: {symbol_dir}")

        stock_item = self._extract_stock(symbol_dir)
        if stock_item is None:
            raise ValueError(f"Could not extract stock data for symbol: {symbol_clean}")

        stocks_file = self.browser_dir / "data" / "stocks.json"
        stocks_list: List[Dict[str, Any]] = []
        if stocks_file.exists():
            try:
                loaded = json.loads(stocks_file.read_text(encoding="utf-8"))
                if isinstance(loaded, list):
                    stocks_list = loaded
            except Exception:
                stocks_list = []

        found_index = -1
        for idx, item in enumerate(stocks_list):
            if isinstance(item, dict) and item.get("symbol") == symbol_clean:
                found_index = idx
                break

        if found_index >= 0:
            stocks_list[found_index] = stock_item
        else:
            stocks_list.append(stock_item)

        self.generate_stocks_json(stocks_list)
        return stock_item


    def scaffold_or_update_ui(self) -> None:
        """Ensures index.html, styles.css, app.js, config.js, schema.sql, and api/ are placed in browser_dir."""
        self.browser_dir.mkdir(parents=True, exist_ok=True)
        (self.browser_dir / "data").mkdir(parents=True, exist_ok=True)
        (self.browser_dir / "api").mkdir(parents=True, exist_ok=True)

        canonical_browser_dir = Path(__file__).resolve().parent.parent.parent / "browser"
        assets = [
            "index.html",
            "styles.css",
            "app.js",
            "config.js",
            "schema.sql",
            "api/submit_request.php",
        ]

        for asset_name in assets:
            dest_file = self.browser_dir / asset_name
            src_file = canonical_browser_dir / asset_name

            if src_file.exists():
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                is_same = False
                try:
                    is_same = dest_file.resolve() == src_file.resolve()
                except Exception:
                    is_same = str(dest_file.absolute()) == str(src_file.absolute())
                if not is_same:
                    dest_file.write_text(
                        src_file.read_text(encoding="utf-8"), encoding="utf-8"
                    )

    def run(self) -> Dict[str, Any]:
        """Executes full UI build and data sync pipeline."""
        self.scaffold_or_update_ui()
        stocks_data = self.scan_and_extract()
        out_path = self.generate_stocks_json(stocks_data)
        return {
            "success": True,
            "stocks_count": len(stocks_data),
            "output_file": str(out_path),
        }


if __name__ == "__main__":
    agent = FrontendAgent()
    result = agent.run()
    print(
        f"Frontend Agent: Extracted {result['stocks_count']} stocks to {result['output_file']}"
    )
