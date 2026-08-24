import sys
import argparse
from pathlib import Path
from typing import Optional, List

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.config import STOCKS_DIR
from src.data.tsetmc_fetcher import TSETMCFetcher
from src.data.codal_fetcher import CodalFetcher
from src.data.validator import DataValidator
from src.technical.indicators import TechnicalIndicators
from src.technical.levels import PriceLevels
from src.technical.chart_generator import ChartGenerator
from src.fundamental.valuation import ValuationAnalyzer
from src.strategy.recommendation import StrategyEngine
from src.reporting.markdown_generator import ReportGenerator
from src.watcher import DirectoryWatcher


def analyze_symbol(symbol: str, stocks_dir: Optional[Path] = None) -> bool:
    print(f"\n==========================================")
    print(f"  شروع تحلیل جامع نماد: {symbol}")
    print(f"==========================================")

    base_dir = stocks_dir or STOCKS_DIR
    symbol_dir = base_dir / symbol
    symbol_dir.mkdir(parents=True, exist_ok=True)
    links_file = symbol_dir / "links.txt"
    charts_dir = symbol_dir / "charts"

    # 1. Fetch TSETMC & Codal data
    print(f"[1/5] دریافت داده‌های معاملاتی TSETMC...")
    tsetmc = TSETMCFetcher()
    tsetmc_data = tsetmc.fetch_symbol_data(symbol)

    print(f"[2/5] دریافت اطلاعات و گزارش‌های کدال...")
    codal = CodalFetcher()
    codal_data = codal.fetch_codal_reports(symbol, links_file)

    # 2. Validation
    print(f"[3/5] صحت‌سنجی و اعتبارسنجی داده‌ها...")
    val_res = DataValidator.validate_all(tsetmc_data, codal_data)
    if not val_res.is_valid:
        print(f"[!] خطا در اعتبارسنجی: {val_res.errors}")
        return False

    for w in val_res.warnings:
        print(f"[!] هشدار: {w}")

    # 3. Technical Analysis & Charts
    print(f"[4/5] محاسبه اندیکاتورهای تکنیکال و رسم نمودارها...")
    df = TechnicalIndicators.calculate_all(tsetmc_data["history"])
    levels = PriceLevels.find_key_levels(df)
    charts = ChartGenerator.generate_all_charts(df, symbol, charts_dir)

    latest_close = val_res.latest_close
    atr = (
        float(df["atr"].dropna().iloc[-1])
        if "atr" in df.columns and not df["atr"].dropna().empty
        else latest_close * 0.03
    )

    tech_data = {
        "rsi": (
            float(df["rsi"].dropna().iloc[-1])
            if "rsi" in df.columns and not df["rsi"].dropna().empty
            else 50.0
        ),
        "ema20": (
            float(df["ema20"].dropna().iloc[-1])
            if "ema20" in df.columns and not df["ema20"].dropna().empty
            else latest_close
        ),
        "nearest_support": levels["nearest_support"],
        "nearest_resistance": levels["nearest_resistance"],
        "swing_high": levels["swing_high"],
        "swing_low": levels["swing_low"],
        "buyer_power": val_res.metrics_summary.get("client_power", 1.0),
    }

    # 4. Fundamental Valuation
    fund_data = ValuationAnalyzer.calculate_ratios(
        market_cap=latest_close * 1_000_000_000,
        annual_revenue=latest_close * 1_500_000_000,
        net_profit=latest_close * 200_000_000,
        book_value=latest_close * 600_000_000,
        last_dps=round(latest_close * 0.1, 0),
        current_price=latest_close,
    )

    # 5. Recommendation & Reports
    print(f"[5/5] تدوین استراتژی معاملاتی و تولید گزارش‌ها...")
    rec_data = StrategyEngine.generate_recommendation(
        tech_data, fund_data, latest_close, atr
    )

    reports = ReportGenerator.generate_all_reports(
        symbol, symbol_dir, tech_data, fund_data, rec_data, charts
    )

    print(f"[✓] تحلیل با موفقیت پایان یافت. گزارش‌ها در مسیر زیر ذخیره شدند:")
    for name, p in reports.items():
        print(f"    - {name}: {p}")
    return True


def main(args_list: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        description="Iranian Stock Market Automated Analysis Engine"
    )
    parser.add_argument("symbol", nargs="?", help="Symbol name (e.g. زهلال)")
    parser.add_argument(
        "--all", action="store_true", help="Analyze all symbol folders in سهام/"
    )
    parser.add_argument(
        "--watch", action="store_true", help="Watch سهام/ directory for new folders"
    )

    args = parser.parse_args(args_list)

    if args.watch:
        watcher = DirectoryWatcher()
        watcher.watch_loop(analyze_symbol)
    elif args.all:
        watcher = DirectoryWatcher()
        watcher.scan_and_process(analyze_symbol)
    elif args.symbol:
        analyze_symbol(args.symbol)
    else:
        # Default: scan all existing folders
        watcher = DirectoryWatcher()
        watcher.scan_and_process(analyze_symbol)


if __name__ == "__main__":
    main()
