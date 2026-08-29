import io
import json
from pathlib import Path
import pandas as pd
import pytest
from src.data.corpus_analyzer import LocalCorpusAnalyzer, CorpusAnalysisResult


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


def test_corpus_analyzer_scans_and_extracts_excel_and_html(tmp_path):
    symbol_dir = tmp_path / "وتجارت"
    codal_dir = symbol_dir / "codal_reports"
    codal_dir.mkdir(parents=True)

    # Create sample excel with standard financial line items
    df = pd.DataFrame({
        "سرفصل": [
            "درآمدهای عملیاتی",
            "سود خالص",
            "مجموع دارایی‌ها",
            "سپرده‌های سرمایه‌گذاری",
            "تسهیلات اعطایی",
        ],
        "مبلغ": [50000, 12000, 1000000, 800000, 600000],
    })
    df.to_excel(codal_dir / "sample_financials.xlsx", index=False)

    # Create sample html disclosure
    (codal_dir / "1_report.html").write_text(
        "<html><head><title>گزارش افشا</title></head><body><h2>افشای بااهمیت واگذاری سهام</h2><p>شرکت اقدام به واگذاری سهام تابعه نمود.</p></body></html>",
        encoding="utf-8",
    )

    analyzer = LocalCorpusAnalyzer()
    res = analyzer.scan_and_analyze(symbol_dir)

    assert isinstance(res, CorpusAnalysisResult)
    assert len(res.excel_metrics) > 0
    assert res.excel_metrics.get("operating_revenue") == 50000.0 or res.excel_metrics.get("درآمدهای عملیاتی") == 50000.0
    assert res.excel_metrics.get("net_profit") == 12000.0 or res.excel_metrics.get("سود خالص") == 12000.0
    assert res.excel_metrics.get("total_assets") == 1000000.0 or res.excel_metrics.get("مجموع دارایی‌ها") == 1000000.0
    assert res.excel_metrics.get("deposits") == 800000.0 or res.excel_metrics.get("سپرده‌ها") == 800000.0
    assert res.excel_metrics.get("loans") == 600000.0 or res.excel_metrics.get("تسهیلات اعطایی") == 600000.0
    assert "واگذاری سهام" in str(res.html_disclosures)
    assert len(res.scanned_files) >= 2


def test_corpus_analyzer_pdf_extraction(tmp_path):
    symbol_dir = tmp_path / "وتجارت"
    codal_dir = symbol_dir / "codal_reports"
    codal_dir.mkdir(parents=True)

    pdf_bytes = _create_minimal_pdf("Auditor Opinion: Conditional remarks on bad debts")
    pdf_file = codal_dir / "auditor_report.pdf"
    pdf_file.write_bytes(pdf_bytes)

    analyzer = LocalCorpusAnalyzer()
    res = analyzer.scan_and_analyze(symbol_dir)

    assert isinstance(res, CorpusAnalysisResult)
    assert len(res.pdf_insights) >= 1
    pdf_item = res.pdf_insights[0]
    assert "Conditional" in pdf_item.get("text", "") or "Auditor" in pdf_item.get("text", "")
    assert pdf_item.get("filename") == "auditor_report.pdf"


def test_corpus_analyzer_news_extraction(tmp_path):
    symbol_dir = tmp_path / "وتجارت"
    news_dir = symbol_dir / "news"
    news_dir.mkdir(parents=True)

    news_html = """
    <html>
      <head><title>رشد چشمگیر تسهیلات بانک تجارت</title></head>
      <body>
        <h1>افزایش سودآوری و جهش درآمدهای کارمزدی</h1>
        <p class="lead">بانک تجارت در ۹ ماهه امسال موفق به ثبت رکورد جدیدی در اعطای تسهیلات شد.</p>
      </body>
    </html>
    """
    (news_dir / "news_01.html").write_text(news_html, encoding="utf-8")

    analyzer = LocalCorpusAnalyzer()
    res = analyzer.scan_and_analyze(symbol_dir)

    assert isinstance(res, CorpusAnalysisResult)
    assert len(res.news_catalysts) >= 1
    news_item = res.news_catalysts[0]
    assert "رشد" in news_item.get("title", "") or "افزایش" in news_item.get("title", "")
    assert "بانک تجارت" in news_item.get("content", "") or "تسهیلات" in news_item.get("content", "")


def test_corpus_analyzer_market_data(tmp_path):
    symbol_dir = tmp_path / "وتجارت"
    market_dir = symbol_dir / "market_data"
    market_dir.mkdir(parents=True)

    # Trade history CSV
    df = pd.DataFrame({
        "date": ["2026-08-01", "2026-08-02", "2026-08-03"],
        "open": [1500, 1520, 1550],
        "high": [1530, 1560, 1600],
        "low": [1490, 1510, 1540],
        "close": [1520, 1550, 1580],
        "volume": [10000000, 15000000, 20000000],
    })
    df.to_csv(market_dir / "trade_history.csv", index=False)

    # Tape JSON
    tape_data = {
        "symbol": "وتجارت",
        "last_price": 1580,
        "buyer_power_ratio": 1.85,
        "individual_buy_per_capita": 45000000,
        "individual_sell_per_capita": 24000000,
        "queue_status": "صف خرید سنگین",
    }
    (market_dir / "orderbook_tape.json").write_text(json.dumps(tape_data, ensure_ascii=False), encoding="utf-8")

    analyzer = LocalCorpusAnalyzer()
    res = analyzer.scan_and_analyze(symbol_dir)

    assert isinstance(res, CorpusAnalysisResult)
    assert res.market_metrics.get("last_close") == 1580.0
    assert res.market_metrics.get("average_volume") == 15000000.0
    assert res.market_metrics.get("buyer_power_ratio") == 1.85
    assert res.market_metrics.get("queue_status") == "صف خرید سنگین"


def test_corpus_analyzer_handles_empty_or_nonexistent_dir(tmp_path):
    analyzer = LocalCorpusAnalyzer()
    
    # Nonexistent dir
    res_none = analyzer.scan_and_analyze(tmp_path / "nonexistent")
    assert isinstance(res_none, CorpusAnalysisResult)
    assert res_none.scanned_files == []
    assert res_none.excel_metrics == {}

    # Empty dir
    empty_dir = tmp_path / "empty_dir"
    empty_dir.mkdir()
    res_empty = analyzer.scan_and_analyze(empty_dir)
    assert isinstance(res_empty, CorpusAnalysisResult)
    assert res_empty.scanned_files == []


def test_corpus_analyzer_handles_corrupt_files(tmp_path):
    symbol_dir = tmp_path / "وتجارت"
    codal_dir = symbol_dir / "codal_reports"
    codal_dir.mkdir(parents=True)

    # Corrupt excel
    (codal_dir / "corrupt.xlsx").write_bytes(b"not an excel file content")
    # Corrupt pdf
    (codal_dir / "corrupt.pdf").write_bytes(b"not a pdf content")
    # Corrupt html
    (codal_dir / "corrupt.html").write_text("<<<>>>", encoding="utf-8")

    analyzer = LocalCorpusAnalyzer()
    res = analyzer.scan_and_analyze(symbol_dir)
    assert isinstance(res, CorpusAnalysisResult)
    # Should not raise exception and continue gracefully
    assert len(res.scanned_files) >= 3


def test_corpus_analyzer_nested_subfolders(tmp_path):
    symbol_dir = tmp_path / "وتجارت"
    nested_dir = symbol_dir / "codal_reports" / "financials" / "2025" / "q3"
    nested_dir.mkdir(parents=True)

    df = pd.DataFrame({
        "سرفصل": ["سود خالص"],
        "مبلغ": [34000],
    })
    df.to_excel(nested_dir / "nested_financials.xlsx", index=False)

    analyzer = LocalCorpusAnalyzer()
    res = analyzer.scan_and_analyze(symbol_dir)
    assert isinstance(res, CorpusAnalysisResult)
    assert res.excel_metrics.get("net_profit") == 34000.0 or res.excel_metrics.get("سود خالص") == 34000.0
