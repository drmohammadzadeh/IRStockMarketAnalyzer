import urllib.parse
from pathlib import Path
import httpx
from typing import Dict, Any, List, Optional
from src.config import HEADERS, REQUEST_TIMEOUT, CODAL_SEARCH_API


class CodalFetcher:
    """Fetcher for Codal financial statements, monthly activity reports, and corporate announcements."""

    def __init__(self, client: Optional[httpx.Client] = None):
        self.client = client or httpx.Client(
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
            verify=False,
            follow_redirects=True,
            trust_env=False,
        )

    @staticmethod
    def extract_symbol_from_file(links_file: Path) -> Optional[str]:
        """Extracts ticker symbol from a links.txt file containing Codal search URLs."""
        if not links_file.exists():
            return None
        content = links_file.read_text(encoding="utf-8", errors="ignore")
        for line in content.splitlines():
            line = line.strip()
            if "Symbol=" in line:
                parsed = urllib.parse.urlparse(line)
                query_params = urllib.parse.parse_qs(parsed.query)
                symbols = query_params.get("Symbol", [])
                if symbols:
                    return symbols[0]
        return None

    @staticmethod
    def categorize_letters(letters: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorizes raw Codal letters into structured report categories."""
        result: Dict[str, List[Dict[str, Any]]] = {
            "financial_statements": [],
            "monthly_reports": [],
            "material_disclosures": [],
            "assemblies": [],
            "capital_increases": [],
            "others": [],
        }
        for l in letters:
            title = l.get("Title", "")
            if "صورت‌های مالی" in title or "صورتهای مالی" in title:
                result["financial_statements"].append(l)
            elif "فعالیت ماهانه" in title:
                result["monthly_reports"].append(l)
            elif "افزایش سرمایه" in title:
                result["capital_increases"].append(l)
            elif "افشای اطلاعات بااهمیت" in title or "شفاف‌سازی" in title:
                result["material_disclosures"].append(l)
            elif "مجمع" in title or "تصمیمات" in title:
                result["assemblies"].append(l)
            else:
                result["others"].append(l)
        return result

    def fetch_codal_reports(self, symbol: str, links_file: Optional[Path] = None) -> Dict[str, Any]:
        """Fetches and categorizes reports for a given symbol from the Codal API."""
        target_symbol = symbol
        if links_file and links_file.exists():
            file_symbol = self.extract_symbol_from_file(links_file)
            if file_symbol:
                target_symbol = file_symbol

        try:
            params = {
                "Symbol": target_symbol,
                "LetterType": "-1",
                "PageNumber": "1",
                "Audited": "true",
                "NotAudited": "true",
                "Category": "-1",
            }
            resp = self.client.get(CODAL_SEARCH_API, params=params)
            letters = []
            if resp.status_code == 200:
                data = resp.json()
                letters = data.get("Letters", [])
            categorized = self.categorize_letters(letters)
            return {
                "symbol": target_symbol,
                "success": True,
                "letters_count": len(letters),
                "categorized": categorized,
                "raw_letters": letters[:20],
            }
        except Exception as e:
            return {
                "symbol": target_symbol,
                "success": False,
                "error": str(e),
                "categorized": self.categorize_letters([]),
            }
