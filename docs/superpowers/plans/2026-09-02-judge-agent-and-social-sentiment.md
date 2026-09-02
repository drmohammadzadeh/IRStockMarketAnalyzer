# پیاده‌سازی ایجنت داور (Judge Agent)، خزش احساسات اجتماعی (سهام‌یاب و ره‌آورد ۳۶۰) و تضمین اصالت و تازگی داده‌ها

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ایجاد ایجنت داور ارشد (`JudgeAgent`) برای ممیزی ۵ ستونه کیفیت، خزش و تحلیل احساسات عمومی در سهام‌یاب و ره‌آورد ۳۶۰، اعتبارسنجی باینری Magic Bytes برای فایل‌های کدال، و اتصال حلقه بازخورد خودترمیمی در ارکستراتور.

**Architecture:** یک خط‌لوله ۵ مرحله‌ای که در انتهای آن `JudgeAgent` خروجی‌های دریافت داده (Crawler)، تلخیص (Summarizer)، تحلیل‌ها (Analysts) و استراتژی (Strategy) را داوری می‌کند. در صورت عدم احراز امتیاز بالای ۸.۵ یا وجود نقص بحرانی، فرآیند به‌صورت خودکار با دستورات اصلاحی تکرار می‌شود.

**Tech Stack:** Python 3.13, httpx, BeautifulSoup4, pandas, pypdf, pytest, jdatetime, git.

## Global Constraints
- نویسنده و توسعه دهنده باید در تمام گزارش‌ها درج شود: `alimohammadzadeh@ut.ac.ir`.
- فایل‌های ذخیره‌شده در `codal_reports/` باید دارای Magic Bytes باینری معتبر باشند (`%PDF-`, `PK`, `ÐÏà`).
- داده‌های شبکه اجتماعی سهام‌یاب و ره‌آورد ۳۶۰ در `news/social_sentiment.json` ذخیره شوند.
- هر ۳ نمودار تحلیلی تکنیکال باید بخش آموزشی برای مبتدیان داشته باشند.
- سیستم امتیازدهی سه‌گانه ($S_1, S_2, S_3, S_{\text{Final}}$) باید بدون نقص محاسبه و در README درج شود.
- تمام آزمون‌های خودکار `pytest` باید ۱۰۰٪ پاس شوند.

---

### Task 1: اعتبارسنجی باینری Magic Bytes و پاک‌سازی فایل‌های فاسد در Crawler و CodalFetcher

**Files:**
- Create/Modify: `src/data/codal_fetcher.py`
- Modify: `src/agents/crawler.py`
- Test: `tests/test_magic_bytes_downloader.py`

**Interfaces:**
- Consumes: URL دانلود فایل از کدال و هدرهای HTTP.
- Produces: `validate_file_magic_bytes(content: bytes, filename: str) -> bool`، رد صفحات HTML خطای سرور و تلاش مجدد برای لینک باینری.

- [ ] **Step 1: نوشتن تست شکست‌خورده (Failing Test)**
ایجاد فایل `tests/test_magic_bytes_downloader.py`:
```python
import pytest
from pathlib import Path
from src.data.codal_fetcher import CodalFetcher

def test_validate_file_magic_bytes_pdf():
    valid_pdf = b"%PDF-1.4
%\xe2\xe3\xcf\xd3
"
    invalid_pdf = b"<!doctype html><html><body>Error</body></html>"
    assert CodalFetcher.validate_file_magic_bytes(valid_pdf, "report.pdf") is True
    assert CodalFetcher.validate_file_magic_bytes(invalid_pdf, "report.pdf") is False

def test_validate_file_magic_bytes_excel():
    valid_xlsx = b"PK\x03\x04\x14\x00\x06\x00"
    valid_xls = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
    invalid_excel = b"<!DOCTYPE HTML PUBLIC"
    assert CodalFetcher.validate_file_magic_bytes(valid_xlsx, "statements.xlsx") is True
    assert CodalFetcher.validate_file_magic_bytes(valid_xls, "statements.xls") is True
    assert CodalFetcher.validate_file_magic_bytes(invalid_excel, "statements.xlsx") is False
```

- [ ] **Step 2: اجرای تست برای اطمینان از شکست**
اجرا: `pytest tests/test_magic_bytes_downloader.py -v`
نتیجه مورد انتظار: FAIL با خطای `AttributeError: type object 'CodalFetcher' has no attribute 'validate_file_magic_bytes'`

- [ ] **Step 3: پیاده‌سازی متد و به‌روزرسانی دانلود در `CodalFetcher` و `CrawlerAgent`**
در `src/data/codal_fetcher.py`:
افزودن متد استاتیک `validate_file_magic_bytes`:
```python
@staticmethod
def validate_file_magic_bytes(content: bytes, filename: str) -> bool:
    if not content or len(content) < 4:
        return False
    lower_fn = filename.lower()
    if lower_fn.endswith(".pdf"):
        return content.startswith(b"%PDF-")
    elif lower_fn.endswith(".xlsx"):
        return content.startswith(b"PK\x03\x04")
    elif lower_fn.endswith(".xls"):
        return content.startswith(b"\xd0\xcf\x11\xe0")
    return True
```
در حلقه دانلود فایل، در صورتی که محتوا اعتبارسنجی نشود، به جای ذخیره آن به عنوان PDF یا اکسل، لینک مستقیم ضمیمه کدال (`https://codal.ir/Reports/DownloadFile.aspx?id=...` یا فرمت اکسل) را فراخوانی کرده و در صورت عدم دریافت باینری واقعی، فایل را دور ریخته و به سراغ گزارش بعدی می‌رود.
همچنین پاک‌سازی فایل‌های فاسدی که قبلاً با شروع `<!d` ذخیره شده بودند.

- [ ] **Step 4: اجرای مجدد تست**
اجرا: `pytest tests/test_magic_bytes_downloader.py -v`
نتیجه مورد انتظار: PASS

- [ ] **Step 5: ثبت کامیت در گیت**
```bash
git add src/data/codal_fetcher.py src/agents/crawler.py tests/test_magic_bytes_downloader.py
git commit -m "feat(crawler): add magic bytes validation and prevent saving HTML error pages as binary files"
```

---

### Task 2: پیاده‌سازی ماژول خزش و تحلیل احساسات اجتماعی سهام‌یاب و ره‌آورد ۳۶۰ (`src/data/social_crawler.py`)

**Files:**
- Create: `src/data/social_crawler.py`
- Test: `tests/test_social_crawler.py`

**Interfaces:**
- Consumes: نام نماد سهم (فارسی).
- Produces: کلاس `SocialSentimentCrawler` با متدهای `fetch_sahamyab_comments`, `fetch_rahavard_comments`, `analyze_sentiment`, و ذخیره در `news/social_sentiment.json`.

- [ ] **Step 1: نوشتن تست شکست‌خورده**
ایجاد فایل `tests/test_social_crawler.py`:
```python
import pytest
from pathlib import Path
from src.data.social_crawler import SocialSentimentCrawler

def test_social_crawler_structure(tmp_path):
    crawler = SocialSentimentCrawler()
    res = crawler.crawl_and_save("کلید", tmp_path)
    assert res["success"] is True
    assert (tmp_path / "news" / "social_sentiment.json").exists()
    sentiment_data = res["data"]
    assert "sahamyab" in sentiment_data
    assert "rahavard365" in sentiment_data
    assert "composite_sentiment_score" in sentiment_data
    assert 0.0 <= sentiment_data["composite_sentiment_score"] <= 10.0
```

- [ ] **Step 2: اجرای تست برای اطمینان از شکست**
اجرا: `pytest tests/test_social_crawler.py -v`
نتیجه: FAIL (ModuleNotFoundError)

- [ ] **Step 3: پیاده‌سازی `SocialSentimentCrawler` در `src/data/social_crawler.py`**
پیاده‌سازی ارتباط با:
1. `https://www.sahamyab.com/guest/twiter/list?v=0.1&hashtag={symbol}&page=0` با هدرهای شبیه‌ساز مرورگر و فال‌بک جستجوی متنی.
2. استخراج کامنت‌ها و تحلیل‌های کاربران از ره‌آورد ۳۶۰ (`site:rahavard365.com {symbol}`).
3. تحلیل قطبیت کلمات مثبت (صف خرید، شارپ، رشد، عالی، حمایت، ارزندگی) و منفی (ریسک، صف فروش، خالی کردند، مقاومت، ریزش، حباب) و محاسبه نمره ۰ تا ۱۰ سنتیمنت.
4. ذخیره ساختاریافته در `news/social_sentiment.json`.

- [ ] **Step 4: اجرای مجدد تست**
اجرا: `pytest tests/test_social_crawler.py -v`
نتیجه: PASS

- [ ] **Step 5: ثبت کامیت در گیت**
```bash
git add src/data/social_crawler.py tests/test_social_crawler.py
git commit -m "feat(sentiment): implement Sahamyab and Rahavard365 social sentiment crawler"
```

---

### Task 3: پیاده‌سازی ایجنت داور ارشد (`JudgeAgent` در `src/agents/judge.py`)

**Files:**
- Create: `src/agents/judge.py`
- Create: `.agents/judge_agent.md`
- Test: `tests/test_judge_agent.py`

**Interfaces:**
- Consumes: مسیر پوشه سهم (`symbol_dir`) و نام نماد (`symbol`).
- Produces: `JudgementVerdict` با امتیاز کل، لیست نواقص بحرانی، اقدامات اصلاحی و گواهی مکتوب داوری (`certificate_markdown`).

- [ ] **Step 1: نوشتن تست شکست‌خورده**
ایجاد فایل `tests/test_judge_agent.py`:
```python
import pytest
from pathlib import Path
from src.agents.judge import JudgeAgent, JudgementVerdict

def test_judge_agent_evaluation_pass(tmp_path):
    # Setup compliant symbol directory with all valid artifacts
    symbol_dir = tmp_path / "سهام" / "تست"
    (symbol_dir / "codal_reports").mkdir(parents=True)
    (symbol_dir / "market_data").mkdir(parents=True)
    (symbol_dir / "news").mkdir(parents=True)
    (symbol_dir / "charts").mkdir(parents=True)

    # Valid magic bytes PDF
    (symbol_dir / "codal_reports" / "report.pdf").write_bytes(b"%PDF-1.4
valid test pdf
")
    (symbol_dir / "codal_reports" / "letters_index.json").write_text("[]", encoding="utf-8")
    
    # Valid trade history and tape
    (symbol_dir / "market_data" / "trade_history.csv").write_text("date,close\n2026-09-01,1000\n", encoding="utf-8")
    (symbol_dir / "market_data" / "orderbook_tape.json").write_text('{"buyer_power": 1.2}', encoding="utf-8")
    
    # Valid social sentiment
    (symbol_dir / "news" / "social_sentiment.json").write_text('{"composite_sentiment_score": 7.5}', encoding="utf-8")
    (symbol_dir / "news" / "news_archive.json").write_text("[]", encoding="utf-8")

    # Valid reports
    (symbol_dir / "technical_report.md").write_text("گزارش تکنیکال\n📚 راهنمای آموزشی", encoding="utf-8")
    (symbol_dir / "fundamental_report.md").write_text("گزارش بنیادی\nسود خالص", encoding="utf-8")
    (symbol_dir / "final_recommendation.md").write_text("جدول جامع امتیازدهی سه‌گانه\n3.5 از ۵", encoding="utf-8")
    (symbol_dir / "strategy_recommendation.json").write_text('{"scoring": {"score_final": 3.5}}', encoding="utf-8")

    judge = JudgeAgent()
    verdict = judge.audit_symbol("تست", symbol_dir)
    assert verdict.is_approved is True
    assert verdict.score >= 8.5
    assert "گواهی تأیید داوری" in verdict.certificate_markdown

def test_judge_agent_rejects_corrupted_pdf(tmp_path):
    symbol_dir = tmp_path / "سهام" / "تست_فاسد"
    (symbol_dir / "codal_reports").mkdir(parents=True)
    # Corrupted PDF with HTML tag
    (symbol_dir / "codal_reports" / "bad.pdf").write_bytes(b"<!doctype html>error")

    judge = JudgeAgent()
    verdict = judge.audit_symbol("تست_فاسد", symbol_dir)
    assert verdict.is_approved is False
    assert any("فایل نامعتبر" in d or "Magic Bytes" in d for d in verdict.critical_defects)
```

- [ ] **Step 2: اجرای تست برای اطمینان از شکست**
اجرا: `pytest tests/test_judge_agent.py -v`
نتیجه: FAIL (ModuleNotFoundError)

- [ ] **Step 3: پیاده‌سازی `JudgeAgent` و `JudgementVerdict` در `src/agents/judge.py`**
پیاده‌سازی ممیزی ۵ ستونه:
1. ستون اصالت فایل‌ها (بررسی بایت‌های آغازین تمام فایل‌های موجود در `codal_reports/`).
2. ستون تازگی معاملات (تطابق تاریخ آخرین رکورد `trade_history.csv` با روزهای اخیر کاری).
3. ستون احساسات اجتماعی (وجود و سلامت `social_sentiment.json`).
4. ستون عمق تحلیلی (وجود راهنمای آموزشی ذیل نمودارها و ارقام بنیادی در گزارش‌ها).
5. ستون امتیازدهی سه‌گانه (محاسبه درست $S_1, S_2, S_3, S_{\text{Final}}$).
ایجاد سند مشخصات در `.agents/judge_agent.md`.

- [ ] **Step 4: اجرای مجدد تست**
اجرا: `pytest tests/test_judge_agent.py -v`
نتیجه: PASS

- [ ] **Step 5: ثبت کامیت در گیت**
```bash
git add src/agents/judge.py .agents/judge_agent.md tests/test_judge_agent.py
git commit -m "feat(judge): implement Supreme Judge Agent with 5-pillar arbitration rubric"
```

---

### Task 4: یکپارچه‌سازی در ارکستراتور (`MultiAgentOrchestrator`) با حلقه بازخورد و داوری نهایی

**Files:**
- Modify: `src/orchestrator.py`
- Modify: `src/agents/__init__.py`
- Modify: `src/agents/crawler.py`
- Modify: `src/agents/summarizer.py`
- Modify: `src/agents/strategy_agent.py`
- Test: `tests/test_orchestrator.py`

**Interfaces:**
- ارکستراتور پس از ۴ مرحله، `judge.audit_symbol` را صدا می‌زند.
- اگر `verdict.is_approved` نباشد، خطاهای داور را چاپ کرده و بر اساس `remedial_actions` چرخه را تکرار می‌کند.
- پس از تأیید، گواهی داوری در `final_recommendation.md` و `README.md` الصاق می‌شود.

- [ ] **Step 1: افزودن تست‌های داوری به `tests/test_orchestrator.py`**
- [ ] **Step 2: اتصال `JudgeAgent` و `SocialSentimentCrawler` در `src/orchestrator.py`**
- [ ] **Step 3: اجرای آزمون‌های `tests/test_orchestrator.py`**
- [ ] **Step 4: ثبت کامیت در گیت**
```bash
git add src/orchestrator.py src/agents/ tests/test_orchestrator.py
git commit -m "feat(orchestrator): integrate Judge Agent with autonomous remedial feedback loop"
```

---

### Task 5: اجرای سراسری، آزمون‌های pytest و به‌روزرسانی کلیه نمادها در سبد سهام

**Files:**
- Execute: به‌روزرسانی ۸ نماد در `سهام/` با ممیزی ۱۰۰٪ داور
- Update: `سهام/README.md`
- Test: تمام ۱۱۵+ تست در `python -m pytest`

- [ ] **Step 1: اجرای آزمون‌های خودکار `pytest` و اطمینان از پاس شدن ۱۰۰٪ آزمون‌ها**
- [ ] **Step 2: اجرای اسکریپت به‌روزرسانی برای تمام ۸ نماد و اخذ گواهی تأیید داوری**
- [ ] **Step 3: به‌روزرسانی داشبورد سراسری `سهام/README.md`**
- [ ] **Step 4: ارسال نهایی کامیت‌ها به گیت‌هاب (`git push origin main`)**
