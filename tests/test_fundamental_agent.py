import json
from pathlib import Path
import pandas as pd
import pytest
from src.agents.fundamental_agent import FundamentalAnalystAgent


def test_fundamental_agent_generates_deep_report(tmp_path):
    symbol_dir = tmp_path / "زهلال"
    symbol_dir.mkdir(parents=True)

    agent = FundamentalAnalystAgent()
    res = agent.run("زهلال", symbol_dir, current_price=47500.0)
    assert res["success"] is True
    assert (symbol_dir / "fundamental_report.md").exists()

    content = (symbol_dir / "fundamental_report.md").read_text(encoding="utf-8")
    assert "تجزیه و تحلیل صورت‌های سود و زیان" in content
    assert "روند حاشیه‌های سودآوری" in content
    assert "ترازنامه، ساختار سرمایه و نقدینگی" in content
    assert "تحلیل گزارش‌های فعالیت ماهانه (تولید و فروش)" in content
    assert "ضرایب ارزش‌گذاری و مقایسه صنعتی" in content
    assert "ریسک‌های کلیدی بنیادی" in content
    assert res["metrics"]["fundamental_score"] > 0


def test_fundamental_agent_with_rich_data(tmp_path):
    symbol_dir = tmp_path / "فولاد"
    codal_dir = symbol_dir / "codal_reports"
    news_dir = symbol_dir / "news"
    market_dir = symbol_dir / "market_data"
    codal_dir.mkdir(parents=True)
    news_dir.mkdir(parents=True)
    market_dir.mkdir(parents=True)

    letters = [
        {"Title": "اطلاعات و صورت‌های مالی میاندوره‌ای دوره ۶ ماهه", "PublishDateTime": "1403/08/15"},
        {"Title": "گزارش فعالیت ماهانه دوره ۱ ماهه منتهی به ۱۴۰۳/۰۸/۳۰", "PublishDateTime": "1403/09/05"},
        {"Title": "تصمیمات مجمع عمومی عادی سالیانه", "PublishDateTime": "1403/04/20"}
    ]
    (codal_dir / "letters_index.json").write_text(json.dumps(letters, ensure_ascii=False), encoding="utf-8")
    (codal_dir / "codal_summaries.md").write_text("# خلاصه کدال\nسودآوری شرکت افزایش یافته است.", encoding="utf-8")

    news_data = [{"title": "تقاضای بالای محصولات فولادی در بورس کالا", "source": "سنا", "date": "1403/08/25", "body": "نرخ شمش فولادی ۵ درصد رشد کرد."}]
    (news_dir / "news_archive.json").write_text(json.dumps(news_data, ensure_ascii=False), encoding="utf-8")
    (news_dir / "news_summary.md").write_text("# تحلیل اخبار\nتقاضای محصولات پایدار است.", encoding="utf-8")

    tape_data = {
        "symbol": "فولاد",
        "pe": 6.2,
        "sector_pe": 7.5,
        "eps": 850.0,
        "market_cap": 800000000000000.0,
        "buyer_power": 1.4,
    }
    (market_dir / "orderbook_tape.json").write_text(json.dumps(tape_data, ensure_ascii=False), encoding="utf-8")

    trade_history = pd.DataFrame({
        "date": ["1403/08/01", "1403/08/02"],
        "close": [5200.0, 5300.0],
        "volume": [10000000, 15000000]
    })
    trade_history.to_csv(market_dir / "trade_history.csv", index=False)

    agent = FundamentalAnalystAgent()
    res = agent.run("فولاد", symbol_dir)

    assert res["success"] is True
    assert res["symbol"] == "فولاد"
    assert "metrics" in res
    metrics = res["metrics"]
    assert metrics["current_price"] == 5300.0
    assert metrics["pe_ratio"] > 0
    assert metrics["fundamental_score"] >= 5.0
    assert "valuation_verdict" in metrics

    report_content = (symbol_dir / "fundamental_report.md").read_text(encoding="utf-8")
    assert "فولاد" in report_content
    assert "ضرایب ارزش‌گذاری و مقایسه صنعتی" in report_content
    assert "امتیازدهی بنیادی و جمع‌بندی ارزندگی" in report_content


def test_fundamental_agent_handles_empty_or_corrupted_inputs(tmp_path):
    symbol_dir = tmp_path / "شستا"
    codal_dir = symbol_dir / "codal_reports"
    news_dir = symbol_dir / "news"
    market_dir = symbol_dir / "market_data"
    codal_dir.mkdir(parents=True)
    news_dir.mkdir(parents=True)
    market_dir.mkdir(parents=True)

    (codal_dir / "letters_index.json").write_text("invalid json", encoding="utf-8")
    (news_dir / "news_archive.json").write_text("{broken", encoding="utf-8")
    (market_dir / "orderbook_tape.json").write_text("not json", encoding="utf-8")
    (market_dir / "trade_history.csv").write_text("corrupted,csv\nxxx", encoding="utf-8")

    agent = FundamentalAnalystAgent()
    res = agent.run("شستا", symbol_dir, current_price=0.0)

    assert res["success"] is True
    assert (symbol_dir / "fundamental_report.md").exists()
    assert res["metrics"]["fundamental_score"] > 0


def test_fundamental_agent_string_path_and_metrics_integrity(tmp_path):
    str_dir = str(tmp_path / "کگل")
    agent = FundamentalAnalystAgent()
    res = agent.run("کگل", str_dir, current_price=3200.0)

    assert res["success"] is True
    assert res["symbol"] == "کگل"
    assert Path(res["report_file"]).exists()

    metrics = res["metrics"]
    required_keys = [
        "fundamental_score",
        "pe_ratio",
        "forward_pe",
        "forward_eps",
        "eps",
        "last_dps",
        "ps_ratio",
        "pb_ratio",
        "dividend_yield_pct",
        "gross_margin_pct",
        "operating_margin_pct",
        "net_margin_pct",
        "monthly_growth_mom_pct",
        "monthly_trend",
        "sector_pe",
        "market_cap",
        "current_price",
        "valuation_verdict",
    ]
    for key in required_keys:
        assert key in metrics, f"Missing metric key: {key}"
        assert metrics[key] is not None


def _create_minimal_pdf(text: str) -> bytes:
    """Helper to create a minimal valid PDF bytes stream containing text."""
    content_stream = f"BT /F1 12 Tf 100 700 Td ({text}) Tj ET".encode("latin1", errors="ignore")
    stream_len = len(content_stream)
    pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<</Font<</F1 4 0 R>>>>/Contents 5 0 R>>endobj\n"
        b"4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
        b"5 0 obj<</Length " + str(stream_len).encode("ascii") + b">>stream\n"
        + content_stream + b"\n"
        b"endstream\nendobj\n"
        b"xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000223 00000 n \n0000000290 00000 n \n"
        b"trailer<</Size 6/Root 1 0 R>>\nstartxref\n384\n%%EOF\n"
    )
    return pdf


def test_fundamental_agent_incorporates_local_corpus_excel_and_pdf(tmp_path):
    symbol_dir = tmp_path / "وتجارت"
    codal_dir = symbol_dir / "codal_reports"
    market_dir = symbol_dir / "market_data"
    codal_dir.mkdir(parents=True)
    market_dir.mkdir(parents=True)

    # 1. Local Excel financial statements
    df = pd.DataFrame({
        "سرفصل": [
            "درآمدهای عملیاتی",
            "سود خالص",
            "مجموع دارایی‌ها",
            "سپرده‌های سرمایه‌گذاری",
            "تسهیلات اعطایی",
            "حقوق صاحبان سهام",
        ],
        "مبلغ": [95000000000.0, 25000000000.0, 800000000000.0, 600000000000.0, 450000000000.0, 150000000000.0],
    })
    df.to_excel(codal_dir / "sample_statements.xlsx", index=False)

    # 2. Local PDF with auditor / capital remarks
    pdf_bytes = _create_minimal_pdf("Auditor Opinion: Conditional remarks on banking loans and capital increase from retained earnings")
    (codal_dir / "auditor_report.pdf").write_bytes(pdf_bytes)

    # 3. Market data
    tape_data = {
        "symbol": "وتجارت",
        "last_price": 2500.0,
        "shares_count": 500000000.0,
    }
    (market_dir / "orderbook_tape.json").write_text(json.dumps(tape_data, ensure_ascii=False), encoding="utf-8")

    agent = FundamentalAnalystAgent()
    res = agent.run("وتجارت", symbol_dir, current_price=2500.0)

    assert res["success"] is True
    assert res["symbol"] == "وتجارت"
    assert (symbol_dir / "fundamental_report.md").exists()

    metrics = res["metrics"]
    # Verify metrics extracted from Excel
    assert metrics.get("operating_revenue") == 95000000000.0 or metrics.get("annual_revenue") == 95000000000.0 or metrics["revenue"] == 95000000000.0
    assert metrics.get("net_profit") == 25000000000.0
    assert metrics.get("total_assets") == 800000000000.0 or metrics.get("deposits") == 600000000000.0

    report = (symbol_dir / "fundamental_report.md").read_text(encoding="utf-8")
    assert "95,000,000,000" in report or "95000000000" in report or "سود خالص" in report
    assert "سپرده" in report or "تسهیلات" in report or "دارایی" in report

