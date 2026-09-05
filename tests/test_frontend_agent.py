import json
import subprocess
import sys
import pytest
from pathlib import Path
from src.agents.frontend_agent import (
    FrontendAgent,
    format_persian_date,
    format_volume,
    to_persian_digits,
)


def test_to_persian_digits():
    assert to_persian_digits("0123456789") == "۰۱۲۳۴۵۶۷۸۹"
    assert to_persian_digits(42) == "۴۲"


def test_format_persian_date():
    assert format_persian_date("2026-07-28") == "۶ مرداد"
    assert format_persian_date("2026-07-29") == "۷ مرداد"
    # Invalid date returns original string
    assert format_persian_date("invalid-date") == "invalid-date"


def test_format_volume():
    assert format_volume(None) == "—"
    assert format_volume(0) == "—"
    assert format_volume(-10) == "—"
    assert format_volume(450) == "450"
    assert format_volume(12500) == "12.5K"
    assert format_volume(3485337.0) == "3.5M"
    assert format_volume(35000000.0) == "35.0M"
    assert format_volume(1245000000.0) == "1.2B"


def test_frontend_agent_initialization(tmp_path):
    stocks_dir = tmp_path / "سهام"
    stocks_dir.mkdir()
    browser_dir = tmp_path / "browser"
    agent = FrontendAgent(stocks_dir=stocks_dir, browser_dir=browser_dir)
    assert agent.stocks_dir == stocks_dir
    assert agent.browser_dir == browser_dir


def test_frontend_agent_extraction(tmp_path):
    stocks_dir = tmp_path / "سهام"
    sym_dir = stocks_dir / "زهلال"
    sym_dir.mkdir(parents=True)
    
    # Create market_data/trade_history.csv
    m_dir = sym_dir / "market_data"
    m_dir.mkdir()
    csv_content = (
        "date,open,high,low,close,last,yesterday,volume,value,trades\n"
        "2026-07-28,43600.0,44650.0,42770.0,44200.0,44250.0,43750.0,4453097.0,196836050280.0,20762.0\n"
        "2026-07-29,43020.0,45050.0,43000.0,49080.0,44380.0,44200.0,3485337.0,153745012270.0,17168.0\n"
    )
    (m_dir / "trade_history.csv").write_text(csv_content, encoding="utf-8")
    
    # Create strategy_recommendation.json
    strat = {
        "symbol": "زهلال",
        "plan": {"current_price": 49080.0}
    }
    (sym_dir / "strategy_recommendation.json").write_text(json.dumps(strat), encoding="utf-8")
    
    # Create sample reports with market cap
    (sym_dir / "technical_report.md").write_text("# گزارش تکنیکال زهلال", encoding="utf-8")
    fund_text = (
        "# گزارش تحلیلی جامع بنیادی و ارزش‌گذاری نماد زهلال\n"
        "**آخرین قیمت:** 49,080 ریال | **ارزش بازار:** **4.91 همت** (49,080,000,000,000 ریال)\n"
    )
    (sym_dir / "fundamental_report.md").write_text(fund_text, encoding="utf-8")
    
    browser_dir = tmp_path / "browser"
    agent = FrontendAgent(stocks_dir=stocks_dir, browser_dir=browser_dir)
    stocks = agent.scan_and_extract()
    
    assert len(stocks) == 1
    stock = stocks[0]
    assert stock["symbol"] == "زهلال"
    assert stock["name"] == "کشت و صنعت و دامپروری صنایع غذایی هلال (کشت و صنعت هلال)"
    assert stock["current_price"] == 49080.0
    assert stock["change_percent"] > 0
    assert len(stock["chart_14d"]) == 2
    assert stock["chart_14d"][0]["date"] == "۶ مرداد"
    assert stock["chart_14d"][0]["price"] == 44200.0
    assert stock["chart_14d"][1]["date"] == "۷ مرداد"
    assert stock["chart_14d"][1]["price"] == 49080.0
    assert "links" in stock
    assert "tsetmc" in stock["links"]
    assert "rahavard" in stock["links"]
    assert "codal" in stock["links"]
    assert "technical_github" in stock["links"]
    assert "fundamental_github" in stock["links"]
    assert "https://github.com/drmohammadzadeh/IRStockMarketAnalyzer/blob/main" in stock["links"]["technical_github"]
    assert "https://github.com/drmohammadzadeh/IRStockMarketAnalyzer/blob/main" in stock["links"]["fundamental_github"]
    assert stock["volume"] == "3.5M"
    assert stock["market_cap"] == "49,080 B"


def test_frontend_agent_generate_json(tmp_path):
    stocks_dir = tmp_path / "سهام"
    stocks_dir.mkdir()
    browser_dir = tmp_path / "browser"
    agent = FrontendAgent(stocks_dir=stocks_dir, browser_dir=browser_dir)
    dummy_data = [{"symbol": "تست", "name": "شرکت تست", "current_price": 1000}]
    out_file = agent.generate_stocks_json(dummy_data)
    assert out_file.exists()
    content = json.loads(out_file.read_text(encoding="utf-8"))
    assert len(content) == 1
    assert content[0]["symbol"] == "تست"
    
    # Assert data/stocks.js was generated for file:// CORS bypass
    js_file = browser_dir / "data" / "stocks.js"
    assert js_file.exists()
    assert "window.STOCKS_DATA =" in js_file.read_text(encoding="utf-8")

    index_file = stocks_dir / "index.json"
    assert index_file.exists()
    index_content = json.loads(index_file.read_text(encoding="utf-8"))
    assert len(index_content) == 1


def test_frontend_agent_run(tmp_path):
    stocks_dir = tmp_path / "سهام"
    stocks_dir.mkdir()
    browser_dir = tmp_path / "browser"
    agent = FrontendAgent(stocks_dir=stocks_dir, browser_dir=browser_dir)
    res = agent.run()
    assert res["success"] is True
    assert res["stocks_count"] == 0
    assert Path(res["output_file"]).exists()


def test_frontend_scaffolding(tmp_path):
    stocks_dir = tmp_path / "سهام"
    stocks_dir.mkdir()
    browser_dir = tmp_path / "browser"
    agent = FrontendAgent(stocks_dir=stocks_dir, browser_dir=browser_dir)
    res = agent.run()
    assert res["success"] is True
    assert (browser_dir / "index.html").exists()
    assert (browser_dir / "styles.css").exists()
    assert (browser_dir / "app.js").exists()
    assert (browser_dir / "config.js").exists()
    assert (browser_dir / "schema.sql").exists()
    assert (browser_dir / "api" / "submit_request.php").exists()
    assert (browser_dir / "data" / "stocks.json").exists()
    assert (browser_dir / "data" / "stocks.js").exists()

    html = (browser_dir / "index.html").read_text(encoding="utf-8")
    assert 'dir="rtl"' in html
    assert 'lang="fa"' in html
    assert "لیست سهام" in html
    assert "افزودن سهم" in html
    assert "جستجوی نماد یا نام سهم..." in html
    assert "فیلتر" in html
    assert ("مرتب‌سازی" in html or "مرتبسازی" in html)
    assert "درخواست تحلیل" in html
    assert "data/stocks.js" in html
    assert "نوع درخواست" in html
    assert "تحلیل مجدد (رایگان" in html
    assert "تحلیل مجدد و بروزرسانی گزارشات فوری" in html
    assert "تحلیلهای من" not in html
    assert "دسترسیها" not in html
    assert "بازار اصلی" not in html

    app_js = (browser_dir / "app.js").read_text(encoding="utf-8")
    assert "btn-reanalyze" in app_js
    assert "درخواست شما ثبت شد." in app_js

    schema_sql = (browser_dir / "schema.sql").read_text(encoding="utf-8")
    assert "tjbir_bourse" in schema_sql
    assert "stock_analysis_requests" in schema_sql


def test_banian_name_is_nian_battery():
    agent = FrontendAgent()
    stocks = agent.scan_and_extract()
    banian = next((s for s in stocks if s["symbol"] == "بانیان"), None)
    assert banian is not None
    assert banian["name"] == "نيان باتري خاوران"


def test_frontend_agent_cli():
    res = subprocess.run(
        [sys.executable, "-m", "src.agents.frontend_agent"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "Frontend Agent" in res.stdout or "stocks.json" in res.stdout


def test_run_portfolio_pipeline_integrates_frontend_agent(monkeypatch):
    import run_portfolio

    called = []

    class DummyVerdict:
        score = 9.0
        status = "APPROVED"
        is_approved = True
        critical_defects = []

    class DummyOrchestrator:
        def __init__(self, **kwargs):
            pass

        def run_pipeline(self, symbol, max_retries=3):
            return True

    class DummyJudge:
        def audit_symbol(self, symbol, symbol_dir):
            return DummyVerdict()

    class DummyFrontendAgent:
        def __init__(self, **kwargs):
            pass

        def run(self):
            called.append(True)
            return {
                "success": True,
                "stocks_count": 8,
                "output_file": "browser/data/stocks.json",
            }

    monkeypatch.setattr(run_portfolio, "MultiAgentOrchestrator", DummyOrchestrator)
    monkeypatch.setattr(run_portfolio, "JudgeAgent", DummyJudge)
    monkeypatch.setattr(run_portfolio, "FrontendAgent", DummyFrontendAgent)
    monkeypatch.setattr(
        run_portfolio.Path, "write_text", lambda self, *args, **kwargs: None
    )

    ret = run_portfolio.main()
    assert ret == 0
    assert len(called) == 1


def test_update_single_stock_existing(tmp_path):
    stocks_dir = tmp_path / "سهام"
    stocks_dir.mkdir(parents=True)
    browser_dir = tmp_path / "browser"
    browser_dir.mkdir(parents=True)
    agent = FrontendAgent(stocks_dir=stocks_dir, browser_dir=browser_dir)

    # Pre-populate stocks.json and stocks.js with 2 stocks (زهلال and وتجارت)
    initial_stocks = [
        {"symbol": "زهلال", "name": "زهلال", "current_price": 40000.0, "change_percent": 1.0},
        {"symbol": "وتجارت", "name": "بانک تجارت", "current_price": 1500.0, "change_percent": -0.5},
    ]
    agent.generate_stocks_json(initial_stocks)

    # Set up mock updated trade_history.csv for زهلال
    sym_dir = stocks_dir / "زهلال"
    sym_dir.mkdir(parents=True)
    m_dir = sym_dir / "market_data"
    m_dir.mkdir(parents=True)
    csv_content = (
        "date,open,high,low,close,last,yesterday,volume,value,trades\n"
        "2026-07-28,43600.0,44650.0,42770.0,44200.0,44250.0,43750.0,4453097.0,196836050280.0,20762.0\n"
        "2026-07-29,43020.0,45050.0,43000.0,49080.0,44380.0,44200.0,3485337.0,153745012270.0,17168.0\n"
    )
    (m_dir / "trade_history.csv").write_text(csv_content, encoding="utf-8")

    # Run agent.update_single_stock("زهلال")
    updated_stock = agent.update_single_stock("زهلال")

    # Assert زهلال is updated in return dict
    assert updated_stock["symbol"] == "زهلال"
    assert updated_stock["current_price"] == 49080.0

    # Assert stocks.json contains 2 stocks with updated current_price
    stocks_json_file = browser_dir / "data" / "stocks.json"
    saved_stocks = json.loads(stocks_json_file.read_text(encoding="utf-8"))
    assert len(saved_stocks) == 2
    zehlal_saved = next(s for s in saved_stocks if s["symbol"] == "زهلال")
    assert zehlal_saved["current_price"] == 49080.0
    tejarat_saved = next(s for s in saved_stocks if s["symbol"] == "وتجارت")
    assert tejarat_saved["current_price"] == 1500.0

    # Assert stocks.js contains updated value while preserving وتجارت
    stocks_js_file = browser_dir / "data" / "stocks.js"
    js_content = stocks_js_file.read_text(encoding="utf-8")
    assert "49080" in js_content
    assert "وتجارت" in js_content

    # Assert stocks_dir / index.json is also updated
    index_file = stocks_dir / "index.json"
    assert index_file.exists()
    index_data = json.loads(index_file.read_text(encoding="utf-8"))
    assert len(index_data) == 2


def test_update_single_stock_new(tmp_path):
    stocks_dir = tmp_path / "سهام"
    stocks_dir.mkdir(parents=True)
    browser_dir = tmp_path / "browser"
    browser_dir.mkdir(parents=True)
    agent = FrontendAgent(stocks_dir=stocks_dir, browser_dir=browser_dir)

    # Pre-populate stocks.json with 1 stock (وتجارت)
    initial_stocks = [
        {"symbol": "وتجارت", "name": "بانک تجارت", "current_price": 1500.0}
    ]
    agent.generate_stocks_json(initial_stocks)

    # Set up mock stock کلید
    sym_dir = stocks_dir / "کلید"
    sym_dir.mkdir(parents=True)
    m_dir = sym_dir / "market_data"
    m_dir.mkdir(parents=True)
    csv_content = (
        "date,open,high,low,close,last,yesterday,volume,value,trades\n"
        "2026-07-29,10000.0,10500.0,9900.0,10200.0,10200.0,10000.0,1000000.0,10200000000.0,500.0\n"
    )
    (m_dir / "trade_history.csv").write_text(csv_content, encoding="utf-8")

    # Run agent.update_single_stock("کلید")
    new_stock = agent.update_single_stock("کلید")

    assert new_stock["symbol"] == "کلید"
    assert new_stock["current_price"] == 10200.0

    # Assert stocks.json now has 2 stocks including کلید
    stocks_json_file = browser_dir / "data" / "stocks.json"
    saved_stocks = json.loads(stocks_json_file.read_text(encoding="utf-8"))
    assert len(saved_stocks) == 2
    symbols = [s["symbol"] for s in saved_stocks]
    assert "وتجارت" in symbols
    assert "کلید" in symbols


def test_update_single_stock_not_found(tmp_path):
    stocks_dir = tmp_path / "سهام"
    stocks_dir.mkdir(parents=True)
    browser_dir = tmp_path / "browser"
    browser_dir.mkdir(parents=True)
    agent = FrontendAgent(stocks_dir=stocks_dir, browser_dir=browser_dir)

    with pytest.raises(FileNotFoundError):
        agent.update_single_stock("ناموجود")

