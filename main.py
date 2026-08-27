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
from src.orchestrator import MultiAgentOrchestrator
from src.watcher import DirectoryWatcher


def analyze_symbol(
    symbol: str,
    stocks_dir: Optional[Path] = None,
    max_retries: int = 3,
) -> bool:
    """Runs the multi-agent analysis pipeline on a symbol."""
    orchestrator = MultiAgentOrchestrator(stocks_dir=stocks_dir)
    return orchestrator.run_pipeline(symbol, max_retries=max_retries)


def main(args_list: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        description="Iranian Stock Market Multi-Agent Analysis Pipeline"
    )
    parser.add_argument("symbol", nargs="?", help="Symbol name (e.g. زهلال)")
    parser.add_argument(
        "--all", action="store_true", help="Analyze all symbol folders in سهام/"
    )
    parser.add_argument(
        "--watch", action="store_true", help="Watch سهام/ directory for new folders"
    )
    parser.add_argument(
        "--retries", type=int, default=3, help="Max quality retry attempts per stage"
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
