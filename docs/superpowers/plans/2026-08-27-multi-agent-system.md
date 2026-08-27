# Multi-Agent Iranian Stock Market Analysis System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a multi-agent analysis architecture with Markdown agent definitions in `.agents/`, specialized crawler/downloader, document & news summarizer, deep technical & fundamental analysts, and an autonomous quality inspector with retry loops.

**Architecture:** 
- Agent definitions in `.agents/*.md` declaring persona, objectives, tools, I/O, and quality rubrics.
- Python execution modules under `src/agents/` (`crawler.py`, `summarizer.py`, `technical_agent.py`, `fundamental_agent.py`, `strategy_agent.py`, `inspector.py`).
- Pipeline orchestrator with quality feedback and retry loop in `src/orchestrator.py`.
- Entry point CLI updated in `main.py`.

**Tech Stack:** Python 3.13+, `httpx`, `beautifulsoup4`, `pandas`, `numpy`, `matplotlib`, `jdatetime`, `pytest`.

## Global Constraints
- All agents defined as `.md` files in `.agents/`.
- Subject-based folder structure under `سهام/<symbol>/`:
  - `codal_reports/` (files + `letters_index.json` + `codal_summaries.md`)
  - `news/` (`news_archive.json` + `news_summary.md`)
  - `market_data/` (`trade_history.csv` + `orderbook_tape.json`)
  - `charts/` (`candlestick_overview.png`, `indicators_momentum.png`, `tape_reading_money_flow.png`)
  - `fundamental_report.md` (exhaustive report)
  - `technical_report.md` (exhaustive report)
  - `final_recommendation.md` (synthesized recommendation)
- Quality gate enforcement: minimum quality score >= 8.0/10; automatic retry up to 3 times per stage if quality criteria are not satisfied.

---

### Task 1: Agent Specification Markdown Documents (`.agents/`)

**Files:**
- Create: `.agents/crawler_agent.md`
- Create: `.agents/summarizer_agent.md`
- Create: `.agents/technical_analyst.md`
- Create: `.agents/fundamental_analyst.md`
- Create: `.agents/strategy_recommender.md`
- Create: `.agents/quality_inspector.md`
- Test: `tests/test_agent_specs.py`

**Interfaces:**
- Produces: 6 markdown specification documents defining roles, tools, prompts, and rubrics.

- [ ] **Step 1: Write test verifying agent specification files exist and contain required YAML/MD sections**

```python
import pytest
from pathlib import Path

AGENT_NAMES = [
    "crawler_agent",
    "summarizer_agent",
    "technical_analyst",
    "fundamental_analyst",
    "strategy_recommender",
    "quality_inspector"
]

def test_all_agent_specs_exist():
    agents_dir = Path(__file__).resolve().parent.parent / ".agents"
    assert agents_dir.exists() and agents_dir.is_dir()
    for name in AGENT_NAMES:
        spec_path = agents_dir / f"{name}.md"
        assert spec_path.exists(), f"Missing agent spec: {name}.md"
        content = spec_path.read_text(encoding="utf-8")
        assert "## نقش و هدف (Role & Objective)" in content
        assert "## ورودی‌ها (Inputs)" in content
        assert "## خروجی‌ها (Outputs)" in content
        assert "## سنجه‌های کیفی (Quality Rubric)" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_agent_specs.py -v`
Expected: FAIL (missing `.agents` or files)

- [ ] **Step 3: Create the 6 agent markdown files under `.agents/`**

Create:
- `.agents/crawler_agent.md`
- `.agents/summarizer_agent.md`
- `.agents/technical_analyst.md`
- `.agents/fundamental_analyst.md`
- `.agents/strategy_recommender.md`
- `.agents/quality_inspector.md`

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_agent_specs.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit agent specifications**

```bash
git add .agents/ tests/test_agent_specs.py
git commit -m "docs(agents): define all 6 agent specifications in .agents/ folder"
```

---

### Task 2: Crawler Agent Module (`src/agents/crawler.py`)

**Files:**
- Create: `src/agents/__init__.py`
- Create: `src/agents/crawler.py`
- Create: `tests/test_crawler_agent.py`

**Interfaces:**
- Produces: `CrawlerAgent.run(symbol: str, symbol_dir: Path) -> dict` saving:
  - `codal_reports/*.html` / `*.json` and `letters_index.json` (past 30 days)
  - `news/news_archive.json`
  - `market_data/trade_history.csv`
  - `market_data/orderbook_tape.json`

- [ ] **Step 1: Write unit tests for CrawlerAgent**

```python
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.agents.crawler import CrawlerAgent

def test_crawler_creates_expected_directories_and_files(tmp_path):
    symbol_dir = tmp_path / "زهلال"
    symbol_dir.mkdir()
    
    crawler = CrawlerAgent()
    with patch.object(crawler, "_fetch_codal_letters", return_value=[{"Title": "گزارش ۶ ماهه", "TracingNo": 123, "PublishDateTime": "1403/08/15", "Url": "http://example.com"}]), \
         patch.object(crawler, "_download_letter_content", return_value="<html>گزارش مالی</html>"), \
         patch.object(crawler, "_fetch_news", return_value=[{"title": "رشد سود زهلال", "source": "سنا", "date": "1403/08/16", "url": "http://sena.ir", "body": "سود سهم رشد کرد"}]), \
         patch.object(crawler, "_fetch_market_data", return_value=({"close": [4500]}, {"buy_real_count": 100})):
        
        res = crawler.run("زهلال", symbol_dir)
        assert res["success"] is True
        assert (symbol_dir / "codal_reports" / "letters_index.json").exists()
        assert (symbol_dir / "news" / "news_archive.json").exists()
        assert (symbol_dir / "market_data" / "trade_history.csv").exists()
        assert (symbol_dir / "market_data" / "orderbook_tape.json").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_crawler_agent.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.agents'`

- [ ] **Step 3: Implement `src/agents/crawler.py`**

Implement Codal letter downloader, news search/scraper across Iranian financial sources with fallback to TSE news, and market data export into CSV/JSON.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_crawler_agent.py -v`
Expected: PASS

- [ ] **Step 5: Commit Crawler Agent**

```bash
git add src/agents/ tests/test_crawler_agent.py
git commit -m "feat(agents): implement crawler and downloader agent for codal, news, and market data"
```

---

### Task 3: Summarizer Agent Module (`src/agents/summarizer.py`)

**Files:**
- Create: `src/agents/summarizer.py`
- Create: `tests/test_summarizer_agent.py`

**Interfaces:**
- Produces: `SummarizerAgent.run(symbol: str, symbol_dir: Path) -> dict` generating:
  - `codal_reports/codal_summaries.md`
  - `news/news_summary.md`

- [ ] **Step 1: Write unit tests for SummarizerAgent**

```python
import pytest
from pathlib import Path
import json
from src.agents.summarizer import SummarizerAgent

def test_summarizer_generates_summaries(tmp_path):
    symbol_dir = tmp_path / "زهلال"
    codal_dir = symbol_dir / "codal_reports"
    news_dir = symbol_dir / "news"
    codal_dir.mkdir(parents=True)
    news_dir.mkdir(parents=True)

    letters = [{"Title": "گزارش فعالیت ماهانه", "PublishDateTime": "1403/08/20", "Url": "http://codal.ir/1"}]
    (codal_dir / "letters_index.json").write_text(json.dumps(letters), encoding="utf-8")
    
    news = [{"title": "افتتاح پروژه جدید", "source": "سنا", "date": "1403/08/21", "body": "پروژه افتتاح شد."}]
    (news_dir / "news_archive.json").write_text(json.dumps(news), encoding="utf-8")

    agent = SummarizerAgent()
    res = agent.run("زهلال", symbol_dir)
    assert res["success"] is True
    assert (codal_dir / "codal_summaries.md").exists()
    assert (news_dir / "news_summary.md").exists()
    
    codal_summary = (codal_dir / "codal_summaries.md").read_text(encoding="utf-8")
    assert "خلاصه نکات کلیدی گزارش‌های کدال" in codal_summary
    
    news_summary = (news_dir / "news_summary.md").read_text(encoding="utf-8")
    assert "خلاصه و تحلیل اخبار" in news_summary
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_summarizer_agent.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.agents.summarizer'`

- [ ] **Step 3: Implement `src/agents/summarizer.py`**

Implement summarization of Codal statements, production/sales monthly reports, material disclosures, news aggregation with sentiment classification (positive/negative/neutral), and write Markdown summaries.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_summarizer_agent.py -v`
Expected: PASS

- [ ] **Step 5: Commit Summarizer Agent**

```bash
git add src/agents/summarizer.py tests/test_summarizer_agent.py
git commit -m "feat(agents): implement summarizer agent for codal reports and news"
```

---

### Task 4: Deep Technical Analyst Agent (`src/agents/technical_agent.py`)

**Files:**
- Create: `src/agents/technical_agent.py`
- Create: `tests/test_technical_agent.py`

**Interfaces:**
- Produces: `TechnicalAnalystAgent.run(symbol: str, symbol_dir: Path) -> dict` generating comprehensive `technical_report.md` and 3 charts in `charts/`.

- [ ] **Step 1: Write unit tests for TechnicalAnalystAgent**

```python
import pytest
import pandas as pd
from pathlib import Path
from src.agents.technical_agent import TechnicalAnalystAgent

def test_technical_agent_generates_deep_report(tmp_path):
    symbol_dir = tmp_path / "زهلال"
    symbol_dir.mkdir(parents=True)
    mkt_dir = symbol_dir / "market_data"
    mkt_dir.mkdir()
    
    dates = pd.date_range("2026-01-01", periods=100)
    df = pd.DataFrame({
        "date": dates,
        "open": [4000.0 + i*5 for i in range(100)],
        "high": [4050.0 + i*5 for i in range(100)],
        "low": [3950.0 + i*5 for i in range(100)],
        "close": [4020.0 + i*5 for i in range(100)],
        "volume": [1000000.0] * 100
    })
    df.to_csv(mkt_dir / "trade_history.csv", index=False)
    
    agent = TechnicalAnalystAgent()
    res = agent.run("زهلال", symbol_dir)
    assert res["success"] is True
    assert (symbol_dir / "technical_report.md").exists()
    
    content = (symbol_dir / "technical_report.md").read_text(encoding="utf-8")
    assert "تحلیل ساختار روند و امواج" in content
    assert "تحلیل سیستم معاملاتی ایچیموکو" in content
    assert "اسیلاتورهای تکانه و واگرایی‌ها" in content
    assert "ترازهای فیبوناچی" in content
    assert "تابلوخوانی و رفتارشناسی حقیقی/حقوقی" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_technical_agent.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.agents.technical_agent'`

- [ ] **Step 3: Implement `src/agents/technical_agent.py`**

Implement deep multi-factor technical analysis, Ichimoku cloud dynamics, divergence diagnostics, Fibonacci clusters, tape reading metrics, chart generation calls, and write detailed `technical_report.md`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_technical_agent.py -v`
Expected: PASS

- [ ] **Step 5: Commit Technical Analyst Agent**

```bash
git add src/agents/technical_agent.py tests/test_technical_agent.py
git commit -m "feat(agents): implement deep technical analyst agent"
```

---

### Task 5: Deep Fundamental Analyst Agent (`src/agents/fundamental_agent.py`)

**Files:**
- Create: `src/agents/fundamental_agent.py`
- Create: `tests/test_fundamental_agent.py`

**Interfaces:**
- Produces: `FundamentalAnalystAgent.run(symbol: str, symbol_dir: Path) -> dict` generating comprehensive `fundamental_report.md`.

- [ ] **Step 1: Write unit tests for FundamentalAnalystAgent**

```python
import pytest
from pathlib import Path
from src.agents.fundamental_agent import FundamentalAnalystAgent

def test_fundamental_agent_generates_deep_report(tmp_path):
    symbol_dir = tmp_path / "زهلال"
    symbol_dir.mkdir(parents=True)
    
    agent = FundamentalAnalystAgent()
    res = agent.run("زهلال", symbol_dir)
    assert res["success"] is True
    assert (symbol_dir / "fundamental_report.md").exists()
    
    content = (symbol_dir / "fundamental_report.md").read_text(encoding="utf-8")
    assert "تجزیه و تحلیل صورت‌های سود و زیان" in content
    assert "روند حاشیه‌های سودآوری" in content
    assert "ترازنامه، ساختار سرمایه و نقدینگی" in content
    assert "تحلیل گزارش‌های فعالیت ماهانه (تولید و فروش)" in content
    assert "ضرایب ارزش‌گذاری و مقایسه صنعتی" in content
    assert "ریسک‌های کلیدی بنیادی" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_fundamental_agent.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.agents.fundamental_agent'`

- [ ] **Step 3: Implement `src/agents/fundamental_agent.py`**

Implement deep statement analysis, margins trend, working capital, monthly production/sales tracking, peer multiples, Forward EPS, DPS yield, risk evaluation, and write detailed `fundamental_report.md`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_fundamental_agent.py -v`
Expected: PASS

- [ ] **Step 5: Commit Fundamental Analyst Agent**

```bash
git add src/agents/fundamental_agent.py tests/test_fundamental_agent.py
git commit -m "feat(agents): implement deep fundamental analyst agent"
```

---

### Task 6: Strategy & Risk Recommender Agent (`src/agents/strategy_agent.py`)

**Files:**
- Create: `src/agents/strategy_agent.py`
- Create: `tests/test_strategy_agent.py`

**Interfaces:**
- Produces: `StrategyAgent.run(symbol: str, symbol_dir: Path, tech_metrics: dict, fund_metrics: dict) -> dict` generating `final_recommendation.md`.

- [ ] **Step 1: Write unit tests for StrategyAgent**

```python
import pytest
from pathlib import Path
from src.agents.strategy_agent import StrategyAgent

def test_strategy_agent_generates_recommendation(tmp_path):
    symbol_dir = tmp_path / "زهلال"
    symbol_dir.mkdir(parents=True)
    
    tech_metrics = {"current_price": 47500.0, "rsi": 55.0, "buyer_power": 2.5, "nearest_support": 46000.0, "nearest_resistance": 52000.0, "swing_high": 58000.0, "atr": 1200.0}
    fund_metrics = {"fundamental_score": 8.5, "pe_ratio": 5.2, "dividend_yield_pct": 12.0}
    
    agent = StrategyAgent()
    res = agent.run("زهلال", symbol_dir, tech_metrics, fund_metrics)
    assert res["success"] is True
    assert (symbol_dir / "final_recommendation.md").exists()
    
    content = (symbol_dir / "final_recommendation.md").read_text(encoding="utf-8")
    assert "جدول راهنمای معامله (Actionable Plan)" in content
    assert "راهبرد در ۳ افق زمانی" in content
    assert "شروط ابطال تحلیل" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_strategy_agent.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.agents.strategy_agent'`

- [ ] **Step 3: Implement `src/agents/strategy_agent.py`**

Implement multi-horizon synthesis, entry zone, TP1/TP2, ATR stop loss, R/R calculation, invalidation triggers, and write formatted `final_recommendation.md`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_strategy_agent.py -v`
Expected: PASS

- [ ] **Step 5: Commit Strategy Agent**

```bash
git add src/agents/strategy_agent.py tests/test_strategy_agent.py
git commit -m "feat(agents): implement strategy and risk recommender agent"
```

---

### Task 7: Quality Inspector Agent & Evaluation Rubric (`src/agents/inspector.py`)

**Files:**
- Create: `src/agents/inspector.py`
- Create: `tests/test_inspector_agent.py`

**Interfaces:**
- Produces: `QualityInspector.inspect_stage(stage_name: str, symbol_dir: Path) -> InspectionResult` returning `is_passed: bool`, `score: float`, `defects: List[str]`, `feedback: str`.

- [ ] **Step 1: Write unit tests for QualityInspector**

```python
import pytest
from pathlib import Path
from src.agents.inspector import QualityInspector, InspectionResult

def test_inspector_passes_healthy_crawler_stage(tmp_path):
    symbol_dir = tmp_path / "زهلال"
    (symbol_dir / "codal_reports").mkdir(parents=True)
    (symbol_dir / "news").mkdir(parents=True)
    (symbol_dir / "market_data").mkdir(parents=True)

    (symbol_dir / "codal_reports" / "letters_index.json").write_text("[]", encoding="utf-8")
    (symbol_dir / "news" / "news_archive.json").write_text("[]", encoding="utf-8")
    (symbol_dir / "market_data" / "trade_history.csv").write_text("date,close\n2026-01-01,1000", encoding="utf-8")
    (symbol_dir / "market_data" / "orderbook_tape.json").write_text("{}", encoding="utf-8")

    inspector = QualityInspector()
    res = inspector.inspect_stage("crawler", symbol_dir)
    assert res.is_passed is True
    assert res.score >= 8.0
    assert len(res.defects) == 0

def test_inspector_fails_missing_files(tmp_path):
    symbol_dir = tmp_path / "زهلال"
    symbol_dir.mkdir()
    inspector = QualityInspector()
    res = inspector.inspect_stage("crawler", symbol_dir)
    assert res.is_passed is False
    assert res.score < 8.0
    assert len(res.defects) > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_inspector_agent.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.agents.inspector'`

- [ ] **Step 3: Implement `src/agents/inspector.py`**

Implement rubrics for:
- `crawler`: verify files exist, non-zero sizes, valid JSON/CSV formats.
- `summarizer`: verify `codal_summaries.md` and `news_summary.md` exist and have non-empty analytical content.
- `analysts`: verify `technical_report.md`, `fundamental_report.md`, and 3 charts exist with sufficient breadth.
- `strategy`: verify `final_recommendation.md` contains signal, entry zone, stop loss, targets, and invalidation terms.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_inspector_agent.py -v`
Expected: PASS

- [ ] **Step 5: Commit Quality Inspector Agent**

```bash
git add src/agents/inspector.py tests/test_inspector_agent.py
git commit -m "feat(agents): implement quality inspector agent and evaluation rubric"
```

---

### Task 8: Pipeline Orchestrator with Quality Retry Loop (`src/orchestrator.py`, `main.py`)

**Files:**
- Create: `src/orchestrator.py`
- Modify: `main.py`
- Create: `tests/test_orchestrator.py`

**Interfaces:**
- Produces: `MultiAgentOrchestrator.run_pipeline(symbol: str, max_retries: int = 3) -> bool` coordinating all agents with quality evaluation and feedback retries at every stage.

- [ ] **Step 1: Write unit tests for Orchestrator**

```python
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.orchestrator import MultiAgentOrchestrator

def test_orchestrator_pipeline_success(tmp_path):
    stocks_dir = tmp_path / "سهام"
    symbol_dir = stocks_dir / "زهلال"
    symbol_dir.mkdir(parents=True)
    
    orch = MultiAgentOrchestrator(stocks_dir=stocks_dir)
    with patch("src.orchestrator.CrawlerAgent.run", return_value={"success": True}), \
         patch("src.orchestrator.SummarizerAgent.run", return_value={"success": True}), \
         patch("src.orchestrator.TechnicalAnalystAgent.run", return_value={"success": True, "metrics": {"current_price": 1000}}), \
         patch("src.orchestrator.FundamentalAnalystAgent.run", return_value={"success": True, "metrics": {"fundamental_score": 8}}), \
         patch("src.orchestrator.StrategyAgent.run", return_value={"success": True}), \
         patch("src.orchestrator.QualityInspector.inspect_stage", return_value=MagicMock(is_passed=True, score=9.0, defects=[])):
        
        success = orch.run_pipeline("زهلال")
        assert success is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_orchestrator.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.orchestrator'`

- [ ] **Step 3: Implement `src/orchestrator.py` and update `main.py`**

Implement sequential agent pipeline:
Crawler -> Inspector (retry up to 3) -> Summarizer -> Inspector (retry up to 3) -> Technical & Fundamental -> Inspector (retry up to 3) -> Strategy -> Final Inspector.
Wire `main.py` to use `MultiAgentOrchestrator`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_orchestrator.py -v`
Expected: PASS

- [ ] **Step 5: Commit Orchestrator**

```bash
git add src/orchestrator.py main.py tests/test_orchestrator.py
git commit -m "feat(orchestrator): implement multi-agent pipeline with autonomous quality gates and retry loops"
```

---

### Task 9: Real-World Execution and End-to-End Verification on `زهلال`

**Files:**
- Execute: `python main.py زهلال`
- Verify outputs:
  - `.agents/*.md` (all 6 specs present)
  - `سهام/زهلال/codal_reports/` (reports + `letters_index.json` + `codal_summaries.md`)
  - `سهام/زهلال/news/` (`news_archive.json` + `news_summary.md`)
  - `سهام/زهلال/market_data/` (`trade_history.csv` + `orderbook_tape.json`)
  - `سهام/زهلال/charts/` (3 PNG charts)
  - `سهام/زهلال/fundamental_report.md`
  - `سهام/زهلال/technical_report.md`
  - `سهام/زهلال/final_recommendation.md`

- [ ] **Step 1: Execute `python main.py زهلال`**

Run: `python main.py زهلال`
Expected: Successful multi-agent execution, all quality gates pass, all files created.

- [ ] **Step 2: Run complete repository test suite**

Run: `python -m pytest -v`
Expected: All tests pass.

- [ ] **Step 3: Commit final generated outputs and updates**

```bash
git add .agents/ src/ tests/ سهام/زهلال/ README.md
git commit -m "feat: complete multi-agent stock analysis system with autonomous quality gates"
```
