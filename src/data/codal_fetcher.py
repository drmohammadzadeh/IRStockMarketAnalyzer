import urllib.parse
from pathlib import Path
import httpx
from typing import Dict, Any, List, Optional, Tuple
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

    @staticmethod
    def validate_file_magic_bytes(content: bytes, filename: str) -> bool:
        """Validates binary magic bytes for PDF and Excel documents.

        Author: alimohammadzadeh@ut.ac.ir
        """
        if not content or len(content) < 4:
            return False
        lower_fn = filename.lower()
        if lower_fn.endswith(".pdf"):
            return content.startswith(b"%PDF-")
        elif lower_fn.endswith(".xlsx"):
            return content.startswith(b"PK\x03\x04") or content.startswith(b"\xd0\xcf\x11\xe0")
        elif lower_fn.endswith(".xls"):
            return content.startswith(b"\xd0\xcf\x11\xe0") or content.startswith(b"PK\x03\x04")
        return True

    @staticmethod
    def get_pdf_urls(letter: Dict[str, Any]) -> List[str]:
        """Returns candidate PDF download URLs for a Codal letter in order of preference.

        Author: alimohammadzadeh@ut.ac.ir
        """
        import re
        urls = []
        if letter.get("PdfUrl"):
            url = str(letter["PdfUrl"]).strip()
            if not url.startswith("http"):
                url = urllib.parse.urljoin("https://codal.ir/", url)
            urls.append(url)

        serial = letter.get("LetterSerial")
        if not serial:
            url_val = str(letter.get("Url", ""))
            if "LetterSerial=" in url_val:
                m = re.search(r"LetterSerial=([^&]+)", url_val)
                if m:
                    serial = m.group(1)

        if serial:
            urls.append(f"https://codal.ir/Reports/DownloadFile.aspx?LetterSerial={serial}&type=pdf")
            urls.append(f"https://codal.ir/Reports/DownloadFile.aspx?LetterSerial={serial}")

        tracing = letter.get("TracingNo")
        if tracing:
            urls.append(f"https://codal.ir/Reports/DownloadFile.aspx?id={tracing}&type=pdf")
            urls.append(f"https://codal.ir/Reports/DownloadFile.aspx?id={tracing}")

        # Remove duplicates while preserving order
        seen = set()
        deduped = []
        for u in urls:
            if u not in seen:
                seen.add(u)
                deduped.append(u)
        return deduped

    @staticmethod
    def get_excel_urls(letter: Dict[str, Any]) -> List[str]:
        """Returns candidate Excel download URLs for a Codal letter in order of preference.

        Author: alimohammadzadeh@ut.ac.ir
        """
        import re
        urls = []
        if letter.get("ExcelUrl"):
            url = str(letter["ExcelUrl"]).strip()
            if not url.startswith("http"):
                url = urllib.parse.urljoin("https://excel.codal.ir/", url)
            urls.append(url)

        serial = letter.get("LetterSerial")
        if not serial:
            url_val = str(letter.get("Url", ""))
            if "LetterSerial=" in url_val:
                m = re.search(r"LetterSerial=([^&]+)", url_val)
                if m:
                    serial = m.group(1)

        if serial:
            urls.append(f"https://excel.codal.ir/service/Excel/GetAll/{serial}")
            urls.append(f"https://codal.ir/Reports/DownloadFile.aspx?LetterSerial={serial}&type=excel")

        tracing = letter.get("TracingNo")
        if tracing:
            urls.append(f"https://excel.codal.ir/service/Excel/GetAll/{tracing}")
            urls.append(f"https://codal.ir/Reports/DownloadFile.aspx?id={tracing}&type=excel")

        seen = set()
        deduped = []
        for u in urls:
            if u not in seen:
                seen.add(u)
                deduped.append(u)
        return deduped

    def download_file(
        self,
        url: str,
        target_path: Optional[Path] = None,
        fallback_urls: Optional[List[str]] = None,
    ) -> Tuple[bool, Optional[bytes], str]:
        """Downloads a file with magic bytes validation and URL fallbacks.

        Author: alimohammadzadeh@ut.ac.ir
        """
        urls_to_try = [url] if url else []
        if fallback_urls:
            for fu in fallback_urls:
                if fu and fu not in urls_to_try:
                    urls_to_try.append(fu)

        if not urls_to_try:
            return False, None, "error"

        target_name = target_path.name if target_path else (url.split("/")[-1].split("?")[0] or "file.bin")

        for u in urls_to_try:
            try:
                resp = self.client.get(u)
                if resp.status_code != 200:
                    continue
                content = resp.content if hasattr(resp, "content") and resp.content else resp.text.encode("utf-8")
                if not content or len(content) < 4:
                    continue

                url_lower = u.lower()
                target_lower = target_name.lower()
                c_type_header = resp.headers.get("content-type", "").lower() if hasattr(resp, "headers") else ""

                if (
                    target_lower.endswith(".pdf")
                    or "type=pdf" in url_lower
                    or url_lower.endswith(".pdf")
                    or "application/pdf" in c_type_header
                ):
                    if self.validate_file_magic_bytes(content, "file.pdf"):
                        if target_path:
                            target_path.parent.mkdir(parents=True, exist_ok=True)
                            target_path.write_bytes(content)
                        return True, content, "pdf"
                    else:
                        continue
                elif (
                    target_lower.endswith((".xlsx", ".xls"))
                    or "excel.codal.ir" in url_lower
                    or "type=excel" in url_lower
                    or "spreadsheet" in c_type_header
                    or "excel" in c_type_header
                ):
                    ext = ".xls" if (target_lower.endswith(".xls") or url_lower.endswith(".xls")) else ".xlsx"
                    if self.validate_file_magic_bytes(content, f"file{ext}"):
                        if target_path:
                            target_path.parent.mkdir(parents=True, exist_ok=True)
                            target_path.write_bytes(content)
                        return True, content, "excel"
                    else:
                        continue
                else:
                    if self.validate_file_magic_bytes(content, target_name):
                        if target_path:
                            target_path.parent.mkdir(parents=True, exist_ok=True)
                            target_path.write_bytes(content)
                        return True, content, "html" if content.lstrip().startswith((b"<!d", b"<html", b"<?xml")) else "bin"
            except Exception:
                continue

        return False, None, "error"

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


def clean_corrupted_codal_reports(base_dir: Path) -> List[Path]:
    """Scans base_dir for corrupted PDF/Excel files in codal_reports directories and removes them.

    Corrupted files are defined as .pdf, .xlsx, or .xls files that start with HTML tags
    (e.g., <!doctype, <html, <?xml) or fail magic byte validation (%PDF-, PK\x03\x04, \xd0\xcf\x11\xe0).

    Author: alimohammadzadeh@ut.ac.ir
    """
    cleaned: List[Path] = []
    base_path = Path(base_dir)
    if not base_path.exists():
        return cleaned

    # Search for all .pdf, .xlsx, .xls files under base_dir (or inside codal_reports)
    if base_path.name == "codal_reports":
        report_files = [f for f in base_path.iterdir() if f.is_file()]
    else:
        report_files = list(base_path.glob("**/codal_reports/*"))

    for report_file in report_files:
        if not report_file.is_file():
            continue
        lower_name = report_file.name.lower()
        if not lower_name.endswith((".pdf", ".xlsx", ".xls")):
            continue

        try:
            content = report_file.read_bytes()
            if not CodalFetcher.validate_file_magic_bytes(content, report_file.name):
                report_file.unlink()
                cleaned.append(report_file)
        except Exception:
            pass

    return cleaned


