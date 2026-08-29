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
    def parse_links_file(links_file: Path) -> Dict[str, List[str]]:
        """Categorizes all URLs present in a links.txt file."""
        categorized = {
            "codal_search": [],
            "codal_direct": [],
            "tsetmc": [],
            "third_party": [],
        }
        if not links_file.exists():
            return categorized
        content = links_file.read_text(encoding="utf-8", errors="ignore")
        for line in content.splitlines():
            line = line.strip()
            if not line or not line.startswith("http"):
                continue
            if "codal.ir/ReportList.aspx" in line:
                categorized["codal_search"].append(line)
            elif "codal.ir" in line:
                categorized["codal_direct"].append(line)
            elif "tsetmc.com" in line:
                categorized["tsetmc"].append(line)
            else:
                categorized["third_party"].append(line)
        return categorized

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
    def extract_inscode_from_file(links_file: Path) -> Optional[str]:
        """Extracts TSETMC inscode from tsetmc links if present in links.txt."""
        if not links_file.exists():
            return None
        content = links_file.read_text(encoding="utf-8", errors="ignore")
        for line in content.splitlines():
            line = line.strip()
            if "tsetmc.com" in line:
                parts = line.split("/")
                for part in parts:
                    clean_part = part.split("?")[0].strip()
                    if clean_part.isdigit() and len(clean_part) >= 12:
                        return clean_part
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

    @staticmethod
    def get_pdf_url(letter: Dict[str, Any]) -> str:
        """Extracts or constructs the PDF download URL for a Codal letter."""
        import re
        if letter.get("PdfUrl"):
            url = str(letter["PdfUrl"]).strip()
            if not url.startswith("http"):
                url = urllib.parse.urljoin("https://codal.ir/", url)
            return url

        serial = letter.get("LetterSerial")
        if not serial:
            url_val = str(letter.get("Url", ""))
            if "LetterSerial=" in url_val:
                m = re.search(r"LetterSerial=([^&]+)", url_val)
                if m:
                    serial = m.group(1)
        if serial:
            return f"https://codal.ir/Reports/DownloadFile.aspx?LetterSerial={serial}&type=pdf"

        tracing = letter.get("TracingNo")
        if tracing:
            return f"https://codal.ir/Reports/DownloadFile.aspx?id={tracing}&type=pdf"
        return ""

    @staticmethod
    def get_excel_url(letter: Dict[str, Any]) -> str:
        """Extracts or constructs the Excel download URL for a Codal letter."""
        import re
        if letter.get("ExcelUrl"):
            url = str(letter["ExcelUrl"]).strip()
            if not url.startswith("http"):
                url = urllib.parse.urljoin("https://excel.codal.ir/", url)
            return url

        serial = letter.get("LetterSerial")
        if not serial:
            url_val = str(letter.get("Url", ""))
            if "LetterSerial=" in url_val:
                m = re.search(r"LetterSerial=([^&]+)", url_val)
                if m:
                    serial = m.group(1)
        if serial:
            return f"https://excel.codal.ir/service/Excel/GetAll/{serial}"

        tracing = letter.get("TracingNo")
        if tracing:
            return f"https://excel.codal.ir/service/Excel/GetAll/{tracing}"
        return ""

    @staticmethod
    def get_html_url(letter: Dict[str, Any]) -> str:
        """Extracts or constructs the HTML announcement URL for a Codal letter."""
        url = letter.get("Url", "")
        if not url:
            return ""
        url = str(url).strip()
        if url.startswith("http"):
            return url
        elif url.startswith("/"):
            return urllib.parse.urljoin("https://codal.ir/", url)
        else:
            return urllib.parse.urljoin("https://codal.ir/Reports/", url)

    def fetch_codal_reports(self, symbol: str, links_file: Optional[Path] = None, max_reports: int = 50) -> Dict[str, Any]:
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
                "raw_letters": letters[:max_reports],
            }
        except Exception as e:
            return {
                "symbol": target_symbol,
                "success": False,
                "error": str(e),
                "categorized": self.categorize_letters([]),
            }

