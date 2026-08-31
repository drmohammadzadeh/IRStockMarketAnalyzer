"""Local corpus file analyzer engine for Iranian stock market data.

نویسنده و توسعه دهنده: alimohammadzadeh@ut.ac.ir
"""

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from bs4 import BeautifulSoup
import pypdf

logger = logging.getLogger(__name__)


@dataclass
class CorpusAnalysisResult:
    """Aggregated analysis results from scanning local files across all directories."""
    excel_metrics: Dict[str, Any] = field(default_factory=dict)
    pdf_insights: List[Dict[str, Any]] = field(default_factory=list)
    html_disclosures: List[Dict[str, Any]] = field(default_factory=list)
    news_catalysts: List[Dict[str, Any]] = field(default_factory=list)
    market_metrics: Dict[str, Any] = field(default_factory=dict)
    scanned_files: List[str] = field(default_factory=list)
    summary_text: str = ""


class LocalCorpusAnalyzer:
    """Recursively scans and analyzes all local files (Excel, PDF, HTML, CSV, JSON) in a stock directory."""

    def __init__(self):
        # Mapping standard financial concept names to Persian keywords
        self.financial_keywords: Dict[str, List[str]] = {
            "operating_revenue": [
                "درآمدهای عملیاتی",
                "درآمد عملیاتی",
                "جمع درآمدهای عملیاتی",
                "درآمد تسهیلات",
                "درآمدهای مشاع",
                "درآمد حاصل از تسهیلات",
                "فروش خالص",
                "درآمد فروش",
                "درآمد ارائه خدمات",
            ],
            "net_profit": [
                "سود خالص",
                "سود (زیان) خالص",
                "سود ویژه",
                "سود خالص دوره",
                "سود (زیان) خالص دوره",
            ],
            "total_assets": [
                "جمع دارایی‌ها",
                "مجموع دارایی‌ها",
                "جمع کل دارایی‌ها",
                "جمع داراییها",
                "کل دارایی‌ها",
            ],
            "deposits": [
                "سپرده‌ها",
                "سپرده‌های سرمایه‌گذاری",
                "جمع بدهی‌ها و سپرده‌ها",
                "سپرده‌های مشتریان",
                "سپرده‌های سرمایه گذاری",
                "سپرده‌های دیداری و پس‌انداز",
            ],
            "loans": [
                "تسهیلات اعطایی",
                "تسهیلات اعطایی و مطالبات",
                "وام‌ها",
                "تسهیلات و تعهدات",
                "تسهیلات",
                "مطالبات از دولت و تسهیلات",
            ],
            "capital": [
                "سرمایه",
                "سرمایه ثبت شده",
                "سرمایه اسمی",
                "سرمایه پرداخت شده",
            ],
            "retained_earnings": [
                "سود انباشته",
                "سود (زیان) انباشته",
            ],
            "equity": [
                "حقوق صاحبان سهام",
                "جمع حقوق صاحبان سهام",
                "حقوق مالکانه",
                "جمع حقوق مالکانه",
                "حقوق مالکانه قابل انتساب به مالکان شرکت اصلی",
            ],
        }

    @staticmethod
    def _normalize_text(text: Any) -> str:
        """Normalizes Persian/Arabic characters and removes non-standard whitespace."""
        if text is None:
            return ""
        s = str(text).strip()
        s = s.replace("ي", "ی").replace("ى", "ی").replace("ك", "ک").replace("ة", "ه").replace("آ", "ا").replace("\u200c", " ")
        return s

    @staticmethod
    def _parse_numeric(val: Any) -> Optional[float]:
        """Converts raw Persian/Arabic strings, formatted numbers, or floats to float."""
        if val is None:
            return None
        if isinstance(val, (int, float)):
            if pd.isna(val):
                return None
            return float(val)

        text = str(val).strip()
        if not text or text.lower() in ("nan", "none", "-", "--", ""):
            return None

        # Convert Persian / Arabic digits
        persian_digits = "۰۱۲۳۴۵۶۷۸۹"
        arabic_digits = "٠١٢٣٤٥٦٧٨٩"
        for i in range(10):
            text = text.replace(persian_digits[i], str(i))
            text = text.replace(arabic_digits[i], str(i))

        # Handle negative in parentheses e.g. (12,345) -> -12345
        is_negative = False
        if text.startswith("(") and text.endswith(")"):
            is_negative = True
            text = text[1:-1].strip()
        elif text.startswith("-"):
            is_negative = True
            text = text[1:].strip()

        # Remove commas, spaces, quotes
        text = text.replace(",", "").replace("،", "").replace(" ", "").replace("'", "").replace('"', "")

        match = re.search(r"[-+]?\d*\.?\d+", text)
        if match:
            try:
                num = float(match.group(0))
                return -num if is_negative else num
            except ValueError:
                return None
        return None

    def _parse_excel(self, file_path: Path) -> Dict[str, Any]:
        """Extracts financial metrics from an Excel or HTML-table spreadsheet file."""
        extracted: Dict[str, Any] = {}
        dataframes: List[pd.DataFrame] = []

        try:
            excel_data = pd.read_excel(file_path, sheet_name=None)
            dataframes = list(excel_data.values())
        except Exception:
            # Codal often serves HTML tables with .xlsx or .xls extensions
            try:
                text = file_path.read_text(encoding="utf-8", errors="ignore")
                soup = BeautifulSoup(text, "html.parser")
                tables = soup.find_all("table")
                for table in tables:
                    rows = []
                    for tr in table.find_all("tr"):
                        cells = [td.get_text().strip() for td in tr.find_all(["td", "th"])]
                        if cells:
                            rows.append(cells)
                    if rows:
                        dataframes.append(pd.DataFrame(rows))
                if not dataframes:
                    try:
                        import io
                        dataframes = pd.read_html(io.StringIO(text), flavor="bs4")
                    except Exception:
                        pass
            except Exception as e:
                logger.warning(f"Error reading Excel/table file {file_path}: {e}")
                return extracted

        full_sample_text = " ".join([str(df.to_string())[:1000] for df in dataframes if df is not None and not df.empty])
        is_million_rials = ("میلیون" in full_sample_text or "میلیون ریال" in full_sample_text)
        if is_million_rials:
            extracted["unit"] = "million_rials"

        for df in dataframes:
            if df is None or df.empty:
                continue

            # Strategy 1: Iterate rows and search for keyword matches
            for row_idx, row in df.iterrows():
                row_items = [self._normalize_text(x) for x in row.values if pd.notna(x)]
                row_text = " ".join(row_items)

                for metric_key, keywords in self.financial_keywords.items():
                    for kw in keywords:
                        kw_norm = self._normalize_text(kw)
                        if kw_norm in row_text:
                            if metric_key == "capital" and any(neg in row_text for neg in ["سرمایه گذاری", "سرمایه گذار", "سهامدار", "شرکت", "عضو"]):
                                continue
                            # Search for numerical values in the row
                            for cell in row.values:
                                num = self._parse_numeric(cell)
                                if num is not None and abs(num) > 0:
                                    should_update = (
                                        metric_key not in extracted
                                        or extracted[metric_key] is None
                                        or (num > extracted[metric_key] and metric_key in ("total_assets", "operating_revenue", "equity", "capital"))
                                    )
                                    if should_update:
                                        extracted[metric_key] = num
                                        extracted[f"{metric_key}_raw"] = num
                                        if is_million_rials:
                                            extracted[f"{metric_key}_unit"] = "million_rials"
                                            extracted[f"{metric_key}_million_rials"] = num
                                            extracted[f"{metric_key}_rials"] = num * 1_000_000.0
                                        else:
                                            extracted[f"{metric_key}_rials"] = num
                                    # Also save by exact keyword found
                                    if kw not in extracted or (num > extracted[kw] and metric_key in ("total_assets", "operating_revenue", "equity", "capital")):
                                        extracted[kw] = num
                                    break

            # Strategy 2: If df has 2 or more columns
            if df.shape[1] >= 2:
                for row_idx, row in df.iterrows():
                    first_cell = self._normalize_text(row.iloc[0])
                    for metric_key, keywords in self.financial_keywords.items():
                        for kw in keywords:
                            kw_norm = self._normalize_text(kw)
                            if kw_norm in first_cell:
                                if metric_key == "capital" and any(neg in first_cell for neg in ["سرمایه گذاری", "سرمایه گذار", "سهامدار", "شرکت", "عضو"]):
                                    continue
                                for col_idx in range(1, df.shape[1]):
                                    num = self._parse_numeric(row.iloc[col_idx])
                                    if num is not None and abs(num) > 0:
                                        should_update = (
                                            metric_key not in extracted
                                            or extracted[metric_key] is None
                                            or (num > extracted[metric_key] and metric_key in ("total_assets", "operating_revenue", "equity", "capital"))
                                        )
                                        if should_update:
                                            extracted[metric_key] = num
                                            extracted[f"{metric_key}_raw"] = num
                                            if is_million_rials:
                                                extracted[f"{metric_key}_unit"] = "million_rials"
                                                extracted[f"{metric_key}_million_rials"] = num
                                                extracted[f"{metric_key}_rials"] = num * 1_000_000.0
                                            else:
                                                extracted[f"{metric_key}_rials"] = num
                                        if kw not in extracted or (num > extracted[kw] and metric_key in ("total_assets", "operating_revenue", "equity", "capital")):
                                            extracted[kw] = num
                                        break

        return extracted

    def _parse_pdf(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Extracts text and key remarks from a PDF file using pypdf."""
        try:
            reader = pypdf.PdfReader(str(file_path))
            pages_text = []
            for idx, page in enumerate(reader.pages):
                try:
                    text = page.extract_text() or ""
                    if text.strip():
                        pages_text.append(text.strip())
                except Exception:
                    continue

            full_text = "\n".join(pages_text)
            if not full_text.strip():
                return None

            # Detect specific insights
            auditor_opinions = []
            capital_increases = []
            board_resolutions = []

            for line in full_text.splitlines():
                line_clean = line.strip()
                if not line_clean:
                    continue
                line_lower = line_clean.lower()
                if any(w in line_clean or w in line_lower for w in ["بندهای شرطی", "اظهارنظر مشروط", "گزارش حسابرس", "نظر حسابرس", "مشروط", "بندهای تاکیدی", "بازرس قانونی", "auditor", "conditional"]):
                    auditor_opinions.append(line_clean)
                if any(w in line_clean or w in line_lower for w in ["افزایش سرمایه", "سود انباشته", "تجدید ارزیابی", "آورده نقدی", "گزارش توجیهی", "capital increase", "retained earnings"]):
                    capital_increases.append(line_clean)
                if any(w in line_clean or w in line_lower for w in ["تصمیمات مجمع", "مصوبات هیئت مدیره", "تقسیم سود", "dps", "هیأت مدیره", "board resolution", "general assembly"]):
                    board_resolutions.append(line_clean)


            return {
                "filename": file_path.name,
                "path": str(file_path),
                "total_pages": len(reader.pages),
                "text": full_text[:4000],  # excerpt for downstream agents
                "auditor_opinions": auditor_opinions[:5],
                "capital_increases": capital_increases[:5],
                "board_resolutions": board_resolutions[:5],
            }
        except Exception as e:
            logger.warning(f"Error reading PDF file {file_path}: {e}")
            return None

    def _parse_html(self, file_path: Path, is_news: bool = False) -> Optional[Dict[str, Any]]:
        """Extracts text, headlines, and disclosures from an HTML file."""
        try:
            content = ""
            for encoding in ("utf-8", "windows-1256", "latin-1"):
                try:
                    content = file_path.read_text(encoding=encoding, errors="ignore")
                    if content:
                        break
                except Exception:
                    continue

            if not content.strip():
                return None

            soup = BeautifulSoup(content, "html.parser")

            # Remove scripts and styles
            for elem in soup(["script", "style", "nav", "footer"]):
                elem.extract()

            # Extract title
            title = ""
            if soup.title and soup.title.string:
                title = soup.title.string.strip()
            elif soup.find("h1"):
                title = soup.find("h1").get_text().strip()
            elif soup.find("h2"):
                title = soup.find("h2").get_text().strip()

            # Extract headings
            headings = [h.get_text().strip() for h in soup.find_all(["h1", "h2", "h3"]) if h.get_text().strip()]

            # Extract paragraphs / body
            paragraphs = [p.get_text().strip() for p in soup.find_all(["p", "article", "div"]) if len(p.get_text().strip()) > 20]
            body_text = "\n".join(paragraphs[:10]) if paragraphs else soup.get_text(separator="\n", strip=True)[:2000]

            sentiment_positive = ["رشد", "افزایش", "سودآوری", "جهش", "رکورد", "مثبت", "توسعه", "پیشرفت", "بهبود"]
            sentiment_negative = ["افت", "کاهش", "زیان", "جریمه", "ریزش", "منفی", "توقف", "بحران", "انحلال"]

            clean_text = (body_text + " " + title).replace("صورت سود و زیان", "").replace("سود و زیان", "").replace("سود (زیان)", "").replace("سود(زیان)", "")
            pos_hits = [w for w in sentiment_positive if w in clean_text]
            neg_hits = [w for w in sentiment_negative if w in clean_text]

            sentiment = "خنثی"
            if len(pos_hits) > len(neg_hits):
                sentiment = "مثبت"
            elif len(neg_hits) > len(pos_hits):
                sentiment = "منفی"

            return {
                "filename": file_path.name,
                "path": str(file_path),
                "title": title or file_path.stem,
                "headings": headings[:5],
                "content": body_text[:3000],
                "sentiment": sentiment,
                "sentiment_keywords": pos_hits + neg_hits,
                "is_news": is_news,
            }
        except Exception as e:
            logger.warning(f"Error reading HTML file {file_path}: {e}")
            return None

    def _parse_market_data(self, symbol_dir: Path) -> Dict[str, Any]:
        """Calculates statistics from trade_history.csv and orderbook_tape.json."""
        metrics: Dict[str, Any] = {}
        market_dir = symbol_dir / "market_data"
        if not market_dir.exists():
            return metrics

        # 1. Trade history CSV
        csv_file = market_dir / "trade_history.csv"
        if csv_file.exists():
            try:
                df = pd.read_csv(csv_file)
                if not df.empty and "close" in df.columns:
                    df["close"] = pd.to_numeric(df["close"], errors="coerce")
                    df = df.dropna(subset=["close"])
                    if not df.empty:
                        metrics["last_close"] = float(df["close"].iloc[-1])
                        metrics["max_price"] = float(df["close"].max())
                        metrics["min_price"] = float(df["close"].min())
                        if "volume" in df.columns:
                            df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0)
                            metrics["average_volume"] = float(df["volume"].mean())
                            metrics["total_volume"] = float(df["volume"].sum())
                        if "date" in df.columns:
                            metrics["last_date"] = str(df["date"].iloc[-1])
                        if len(df) > 1:
                            first_close = float(df["close"].iloc[0])
                            last_close = float(df["close"].iloc[-1])
                            if first_close > 0:
                                metrics["period_price_change_pct"] = round(((last_close - first_close) / first_close) * 100, 2)
            except Exception as e:
                logger.warning(f"Error parsing trade history in {market_dir}: {e}")

        # 2. Tape JSON
        tape_file = market_dir / "orderbook_tape.json"
        if tape_file.exists():
            try:
                content = tape_file.read_text(encoding="utf-8")
                tape_data = json.loads(content)
                if isinstance(tape_data, dict):
                    for k in [
                        "buyer_power_ratio",
                        "individual_buy_per_capita",
                        "individual_sell_per_capita",
                        "queue_status",
                        "individual_buy_volume",
                        "individual_sell_volume",
                        "legal_buy_volume",
                        "legal_sell_volume",
                    ]:
                        if k in tape_data:
                            metrics[k] = tape_data[k]
            except Exception as e:
                logger.warning(f"Error parsing orderbook tape in {market_dir}: {e}")

        return metrics

    def scan_and_analyze(self, symbol_dir: Union[str, Path]) -> CorpusAnalysisResult:
        """Recursively scans all files in symbol_dir and returns structured CorpusAnalysisResult."""
        target_dir = Path(symbol_dir)
        if not target_dir.exists() or not target_dir.is_dir():
            return CorpusAnalysisResult()

        scanned_files: List[str] = []
        aggregated_excel: Dict[str, Any] = {}
        pdf_insights: List[Dict[str, Any]] = []
        html_disclosures: List[Dict[str, Any]] = []
        news_catalysts: List[Dict[str, Any]] = []

        # Recursively walk all files, prioritizing consolidated parent statements and monthly reports
        all_files = [p for p in target_dir.rglob("*") if p.is_file()]
        def file_sort_key(p: Path):
            name = p.name.lower()
            is_parent = 0 if ("ماهانه" in name or "تلفیقی" in name or "اصلی" in name) else 1
            import re
            m = re.match(r"^(\d+)_", name)
            prefix = int(m.group(1)) if m else 999
            return (is_parent, prefix, str(p))

        all_files.sort(key=file_sort_key)

        for p in all_files:

            rel_str = str(p.relative_to(target_dir))
            scanned_files.append(rel_str)
            ext = p.suffix.lower()

            # Determine file type
            if ext in (".xlsx", ".xls"):
                excel_res = self._parse_excel(p)
                for k, v in excel_res.items():
                    if k not in aggregated_excel or aggregated_excel[k] is None:
                        aggregated_excel[k] = v
                    elif isinstance(v, (int, float)) and isinstance(aggregated_excel[k], (int, float)):
                        # If a parent company report has larger scale figures for a key metric, prefer the larger parent metric
                        if v > aggregated_excel[k] and ("ماهانه" in p.name or "تلفیقی" in p.name or "اصلی" in p.name):
                            aggregated_excel[k] = v

            elif ext == ".pdf":
                pdf_res = self._parse_pdf(p)
                if pdf_res:
                    pdf_insights.append(pdf_res)

            elif ext in (".html", ".htm"):
                is_news_dir = "news" in [part.lower() for part in p.parts]
                html_res = self._parse_html(p, is_news=is_news_dir)
                if html_res:
                    if is_news_dir:
                        news_catalysts.append(html_res)
                    else:
                        html_disclosures.append(html_res)

        # Parse market data
        market_metrics = self._parse_market_data(target_dir)

        # Generate summary text overview
        summary_lines = [
            f"مجموع فایل‌های اسکن‌شده در پوشه محلی: {len(scanned_files)} فایل",
            f"- تعداد گزارش‌های مالی اکسل استخراج‌شده: {len([f for f in scanned_files if f.lower().endswith(('.xlsx', '.xls'))])}",
            f"- تعداد اسناد PDF پردازش‌شده: {len(pdf_insights)}",
            f"- تعداد افشاهای HTML کدال: {len(html_disclosures)}",
            f"- تعداد اخبار و تحلیل‌های وب: {len(news_catalysts)}",
        ]
        if aggregated_excel:
            summary_lines.append("\nشاخص‌های مالی استخراج‌شده از اکسل:")
            for k in ["operating_revenue", "net_profit", "total_assets", "deposits", "loans"]:
                if k in aggregated_excel:
                    summary_lines.append(f"  * {k}: {aggregated_excel[k]:,}")

        summary_text = "\n".join(summary_lines)

        return CorpusAnalysisResult(
            excel_metrics=aggregated_excel,
            pdf_insights=pdf_insights,
            html_disclosures=html_disclosures,
            news_catalysts=news_catalysts,
            market_metrics=market_metrics,
            scanned_files=scanned_files,
            summary_text=summary_text,
        )
