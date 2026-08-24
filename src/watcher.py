import time
from pathlib import Path
from typing import Callable, Set
from src.config import STOCKS_DIR


class DirectoryWatcher:
    """Monitors the stocks directory for existing and newly created symbol folders."""

    def __init__(self, stocks_dir: Path = STOCKS_DIR):
        self.stocks_dir = Path(stocks_dir)
        self.processed: Set[str] = set()

    def scan_and_process(self, process_fn: Callable[[str], bool]) -> None:
        """Scans the stocks directory and processes all existing symbol subfolders."""
        if not self.stocks_dir.exists():
            self.stocks_dir.mkdir(parents=True, exist_ok=True)

        for folder in sorted(self.stocks_dir.iterdir()):
            if folder.is_dir() and not folder.name.startswith("."):
                symbol = folder.name
                process_fn(symbol)
                self.processed.add(symbol)

    def watch_loop(
        self,
        process_fn: Callable[[str], bool],
        poll_interval: int = 5,
        max_iterations: int = 0,
    ) -> None:
        """Continuously watches the directory for new stock folders and processes them."""
        if not self.stocks_dir.exists():
            self.stocks_dir.mkdir(parents=True, exist_ok=True)

        print(f"[*] Watching directory {self.stocks_dir} for new stock folders...")
        iterations = 0
        while True:
            for folder in sorted(self.stocks_dir.iterdir()):
                if (
                    folder.is_dir()
                    and not folder.name.startswith(".")
                    and folder.name not in self.processed
                ):
                    print(f"[+] New stock folder detected: {folder.name}")
                    try:
                        success = process_fn(folder.name)
                        if success:
                            self.processed.add(folder.name)
                    except Exception as e:
                        print(f"[-] Error processing {folder.name}: {e}")

            iterations += 1
            if max_iterations > 0 and iterations >= max_iterations:
                break

            time.sleep(poll_interval)
