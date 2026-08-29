# Deep Crawler, Local Corpus Analyzer & Visual Standards Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a depth-2 recursive crawler for `links.txt` (capping at 50 files with at least 20 PDF/XLSX reports), build a multi-format `LocalCorpusAnalyzer` to parse all local files across directories and subdirectories, eliminate the AI-generated dashboard image to guarantee 100% data accuracy, and verify on `وتجارت`.

**Architecture:** A two-level recursive crawler extracts child links and pointed-to documents (PDF, Excel, HTML) into target directories. A newly introduced `LocalCorpusAnalyzer` engine walks the local folder tree, extracts structured financial and text data from `.xlsx`, `.xls`, `.pdf`, `.html`, `.csv`, and `.json` files, and supplies this corpus to the Summarizer and Fundamental Analyst agents. The AI dashboard image is completely eliminated, relying solely on 3 verified mathematical Matplotlib technical charts.

**Tech Stack:** Python 3.13, httpx, BeautifulSoup4, pandas, openpyxl, pypdf, matplotlib, pytest.

## Global Constraints

- Crawl depth strictly capped at 2 (Level 1: source URLs in `links.txt`, Level 2: child links/document downloads).
- Total file download cap: maximum 50 files per symbol run.
- Minimum official reports quota: at least 20 newest stock reports downloaded in PDF or XLSX/XLS format.
- Complete removal of AI dashboard generation and image references (`ai_dashboard.png`).
- 100% real numerical accuracy from TSETMC and Codal data; no AI hallucinations or fake numbers.
- Author attribution invariant: `نویسنده و توسعه دهنده: alimohammadzadeh@ut.ac.ir`.
- All 96 existing unit tests plus new tests must pass.

---

### Task 1: Complete Elimination of AI Dashboard Generation and References

**Files:**
- Delete: `سهام/زهلال/charts/ai_dashboard.png`, `سهام/فسازان/charts/ai_dashboard.png`, `سهام/وتجارت/charts/ai_dashboard.png`
- Modify: `src/agents/technical_agent.py:306-318`
- Modify: `src/reporting/markdown_generator.py:150-160`
- Modify: `سهام/زهلال/README.md:7-15`
- Modify: `سهام/وتجارت/README.md:7-15`
- Test: `tests/test_no_ai_dashboard.py`

**Interfaces:**
- Consumes: None
- Produces: Clean report generators that reference only the 3 mathematical Matplotlib charts.

- [ ] **Step 1: Write the test verifying no AI dashboard is generated or referenced**

```python
# tests/test_no_ai_dashboard.py
from pathlib import Path
from src.agents.technical_agent import TechnicalAnalystAgent
from src.reporting.markdown_generator import MarkdownReportGenerator

def test_technical_report_has_no_ai_dashboard_reference():
    agent = TechnicalAnalystAgent()
    content = agent.generate_report("وتجارت", {}, {}, [], [])
    assert "ai_dashboard.png" not in content
    assert "candlestick_overview.png" in content
    assert "indicators_momentum.png" in content
    assert "tape_reading_money_flow.png" in content

def test_markdown_generator_has_no_ai_dashboard_reference():
    gen = MarkdownReportGenerator()
    content = gen.generate_technical_report("وتجارت", {}, {})
    assert "ai_dashboard.png" not in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_no_ai_dashboard.py -v`
Expected: FAIL with `assert "ai_dashboard.png" not in content`

- [ ] **Step 3: Remove ai_dashboard references and delete existing images**

Remove `ai_dashboard.png` line from `src/agents/technical_agent.py` and `src/reporting/markdown_generator.py`.
Delete `ai_dashboard.png` from `سهام/زهلال/charts/`, `سهام/فسازان/charts/`, and `سهام/وتجارت/charts/`.
Remove the dashboard section from `سهام/زهلال/README.md` and `سهام/وتجارت/README.md`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_no_ai_dashboard.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ tests/ سهام/
git commit -m "refactor: eliminate AI dashboard generation and image references"
```

---

### Task 2: Depth-2 Recursive Crawler with PDF/XLSX Quota Management

**Files:**
- Modify: `src/data/codal_fetcher.py`
- Modify: `src/agents/crawler.py`
- Test: `tests/test_crawler_agent.py`

**Interfaces:**
- Consumes: `links.txt` containing URLs.
- Produces: `codal_reports/` populated with at least 20 PDF or XLSX/XLS reports plus HTML files, `news/` populated with articles, max 50 files total.

- [ ] **Step 1: Write test for recursive depth-2 crawling and quota enforcement**

```python
# In tests/test_crawler_agent.py
def test_crawler_recursive_depth_and_file_cap(tmp_path):
    symbol_dir = tmp_path / "وتجارت"
    symbol_dir.mkdir(parents=True)
    links_file = symbol_dir / "links.txt"
    links_file.write_text("https://example.com/portal\n", encoding="utf-8")

    crawler = CrawlerAgent()
    # Mock network calls to simulate 2-level linking and document links
    # Verify downloaded files <= 50
    res = crawler.run("وتجارت", symbol_dir)
    assert res["success"] is True
    assert res["total_downloaded_files"] <= 50
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_crawler_agent.py::test_crawler_recursive_depth_and_file_cap -v`
Expected: FAIL

- [ ] **Step 3: Implement recursive depth-2 crawling and quota enforcement in CrawlerAgent**

Enhance `CrawlerAgent`:
1. `_crawl_links_recursively(links, symbol_dir, max_files=50, min_reports=20)`:
   - Level 1: Fetch source page from `links.txt`.
   - Level 2: Extract child links and document links.
   - For Codal: query letters, extract PDF links (`DownloadFile.aspx`) and Excel links (`excel.codal.ir/service/Excel/GetAll/...`), and download at least 20 newest reports in PDF/XLSX into `codal_reports/`.
   - For news/portals: download child articles into `news/`.
   - Cap total downloaded files across directories to 50.
2. Sanitize filenames for Windows compatibility.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_crawler_agent.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add src/agents/crawler.py src/data/codal_fetcher.py tests/test_crawler_agent.py
git commit -m "feat: implement depth-2 recursive crawler with PDF/XLSX quotas"
```

---

### Task 3: Local Corpus File Analyzer Engine (`src/data/corpus_analyzer.py`)

**Files:**
- Create: `src/data/corpus_analyzer.py`
- Test: `tests/test_corpus_analyzer.py`

**Interfaces:**
- Consumes: Local file tree under `سهام/<symbol>/` (`codal_reports/`, `news/`, `market_data/`).
- Produces: `CorpusAnalysisResult` dataclass containing:
  * `excel_metrics`: Extracted balance sheet and income statement metrics.
  * `pdf_insights`: Text extractions, auditor remarks, board resolutions.
  * `html_disclosures`: Extracted announcements and notes.
  * `news_catalysts`: Headlines, news sentiment, and legal/regulatory events.
  * `market_metrics`: OHLCV statistics, buyer power, volume averages.

- [ ] **Step 1: Write the failing tests for LocalCorpusAnalyzer**

```python
# tests/test_corpus_analyzer.py
from pathlib import Path
import pandas as pd
from src.data.corpus_analyzer import LocalCorpusAnalyzer, CorpusAnalysisResult

def test_corpus_analyzer_scans_and_extracts_excel_and_html(tmp_path):
    symbol_dir = tmp_path / "وتجارت"
    codal_dir = symbol_dir / "codal_reports"
    codal_dir.mkdir(parents=True)
    
    # Create sample excel
    df = pd.DataFrame({"سرفصل": ["درآمدهای عملیاتی", "سود خالص"], "مبلغ": [50000, 12000]})
    df.to_excel(codal_dir / "sample_financials.xlsx", index=False)
    
    # Create sample html
    (codal_dir / "1_report.html").write_text("<html><body><h2>افشای بااهمیت واگذاری سهام</h2></body></html>", encoding="utf-8")
    
    analyzer = LocalCorpusAnalyzer()
    res = analyzer.scan_and_analyze(symbol_dir)
    assert isinstance(res, CorpusAnalysisResult)
    assert len(res.excel_metrics) > 0
    assert "واگذاری سهام" in str(res.html_disclosures)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_corpus_analyzer.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.data.corpus_analyzer'`

- [ ] **Step 3: Implement LocalCorpusAnalyzer in `src/data/corpus_analyzer.py`**

Implement:
- `CorpusAnalysisResult` dataclass.
- `LocalCorpusAnalyzer.scan_and_analyze(symbol_dir: Path) -> CorpusAnalysisResult`:
  * Walk all subdirectories recursively.
  * Read `.xlsx` and `.xls` with `pandas.read_excel`.
  * Read `.pdf` with `pypdf` (extract text).
  * Read `.html` and `.htm` with `BeautifulSoup` (extract text and headings).
  * Read `trade_history.csv` and `orderbook_tape.json`.
  * Return structured `CorpusAnalysisResult`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_corpus_analyzer.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/data/corpus_analyzer.py tests/test_corpus_analyzer.py
git commit -m "feat: implement LocalCorpusAnalyzer for multi-format local file corpus"
```

---

### Task 4: Integration of Corpus Analyzer into Summarizer and Fundamental Analyst Agents

**Files:**
- Modify: `src/agents/summarizer.py`
- Modify: `src/agents/fundamental_agent.py`
- Test: `tests/test_summarizer_agent.py`
- Test: `tests/test_fundamental_agent.py`

**Interfaces:**
- Consumes: `LocalCorpusAnalyzer.scan_and_analyze(symbol_dir)`
- Produces: Reports grounded in 100% of the downloaded local files.

- [ ] **Step 1: Write test verifying agents use local corpus analysis**

```python
# In tests/test_summarizer_agent.py & tests/test_fundamental_agent.py
def test_summarizer_incorporates_local_corpus(tmp_path):
    symbol_dir = tmp_path / "وتجارت"
    (symbol_dir / "codal_reports").mkdir(parents=True)
    (symbol_dir / "news").mkdir(parents=True)
    (symbol_dir / "codal_reports" / "report.html").write_text("افزایش سرمایه ۲۵ درصدی از محل سود انباشته", encoding="utf-8")
    
    agent = SummarizerAgent()
    summary = agent.run("وتجارت", symbol_dir)
    assert "سود انباشته" in summary["codal_summary"] or "افزایش سرمایه" in summary["codal_summary"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_summarizer_agent.py -v`
Expected: FAIL

- [ ] **Step 3: Update SummarizerAgent and FundamentalAnalystAgent to use LocalCorpusAnalyzer**

In `src/agents/summarizer.py`:
- Use `LocalCorpusAnalyzer.scan_and_analyze(symbol_dir)` to summarize all HTML, PDF, and Excel documents.
In `src/agents/fundamental_agent.py`:
- Use `LocalCorpusAnalyzer.scan_and_analyze(symbol_dir)` to extract revenue, profit, asset, and banking metrics from Excel and PDF files into `fundamental_report.md`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_summarizer_agent.py tests/test_fundamental_agent.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/agents/summarizer.py src/agents/fundamental_agent.py tests/
git commit -m "feat: integrate LocalCorpusAnalyzer into Summarizer and Fundamental Analyst"
```

---

### Task 5: End-to-End Execution and Verification on `وتجارت`

**Files:**
- Output: `سهام/وتجارت/`
- Test: Full test suite `python -m pytest`

**Interfaces:**
- Consumes: CLI command `python main.py وتجارت`
- Produces: Clean, audited execution with 100% of files crawled and analyzed, 3 mathematical charts, no AI dashboard, and 10/10 quality score.

- [ ] **Step 1: Run complete pytest suite**

Run: `python -m pytest -v`
Expected: All 98+ tests pass.

- [ ] **Step 2: Execute pipeline for وتجارت**

Run: `python main.py وتجارت`
Expected: All 4 stages pass with QualityInspector score 10.0/10.

- [ ] **Step 3: Verify output files in `سهام/وتجارت/`**

Verify:
- `codal_reports/`: Contains at least 20 PDF and XLSX/XLS files.
- `news/`: Contains downloaded HTML news files.
- `charts/`: Contains only `candlestick_overview.png`, `indicators_momentum.png`, `tape_reading_money_flow.png`. No `ai_dashboard.png`.
- `README.md` and `technical_report.md`: No references to AI dashboard.
- `fundamental_report.md`: Real numbers extracted from Excel and Codal reports.

- [ ] **Step 4: Commit and finalize**

```bash
git add -A
git commit -m "feat: verify and finalize deep crawler, corpus analyzer, and visual standards for Vtejarat"
```
