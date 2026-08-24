import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
from src.watcher import DirectoryWatcher
from src.data.validator import ValidationResult
import main


def test_directory_watcher_scan(tmp_path):
    stocks_dir = tmp_path / "سهام"
    stocks_dir.mkdir()
    (stocks_dir / "زهلال").mkdir()
    (stocks_dir / "فولاد").mkdir()
    (stocks_dir / ".hidden").mkdir()
    (stocks_dir / "notes.txt").write_text("not a dir", encoding="utf-8")

    processed = []
    watcher = DirectoryWatcher(stocks_dir=stocks_dir)
    watcher.scan_and_process(lambda s: processed.append(s))

    assert "زهلال" in processed
    assert "فولاد" in processed
    assert ".hidden" not in processed
    assert "notes.txt" not in processed
    assert len(processed) == 2
    assert "زهلال" in watcher.processed
    assert "فولاد" in watcher.processed


def test_directory_watcher_creates_directory_if_not_exists(tmp_path):
    stocks_dir = tmp_path / "non_existing_stocks"
    watcher = DirectoryWatcher(stocks_dir=stocks_dir)
    processed = []
    watcher.scan_and_process(lambda s: processed.append(s))

    assert stocks_dir.exists()
    assert len(processed) == 0


def test_directory_watcher_watch_loop(tmp_path):
    stocks_dir = tmp_path / "سهام"
    stocks_dir.mkdir()
    (stocks_dir / "فملی").mkdir()

    processed = []

    def mock_process(symbol: str) -> bool:
        processed.append(symbol)
        return True

    watcher = DirectoryWatcher(stocks_dir=stocks_dir)
    # Run watch loop for 1 iteration
    watcher.watch_loop(mock_process, poll_interval=0, max_iterations=1)

    assert "فملی" in processed
    assert "فملی" in watcher.processed

    # Second iteration with new folder
    (stocks_dir / "خودرو").mkdir()
    watcher.watch_loop(mock_process, poll_interval=0, max_iterations=1)

    assert processed == ["فملی", "خودرو"]
    assert "خودرو" in watcher.processed


def test_directory_watcher_watch_loop_error_handling(tmp_path):
    stocks_dir = tmp_path / "سهام"
    stocks_dir.mkdir()
    (stocks_dir / "شپنا").mkdir()

    def failing_process(symbol: str) -> bool:
        raise ValueError("Simulated processing failure")

    watcher = DirectoryWatcher(stocks_dir=stocks_dir)
    # Should catch exception and not crash
    watcher.watch_loop(failing_process, poll_interval=0, max_iterations=1)

    assert "شپنا" not in watcher.processed


@patch("main.ReportGenerator.generate_all_reports")
@patch("main.StrategyEngine.generate_recommendation")
@patch("main.ValuationAnalyzer.calculate_ratios")
@patch("main.ChartGenerator.generate_all_charts")
@patch("main.PriceLevels.find_key_levels")
@patch("main.TechnicalIndicators.calculate_all")
@patch("main.DataValidator.validate_all")
@patch("main.CodalFetcher")
@patch("main.TSETMCFetcher")
def test_analyze_symbol_success(
    mock_tsetmc_cls,
    mock_codal_cls,
    mock_validate_all,
    mock_calc_tech,
    mock_find_levels,
    mock_gen_charts,
    mock_calc_fund,
    mock_gen_rec,
    mock_gen_reports,
    tmp_path,
):
    # Mock TSETMC & Codal fetchers
    mock_tsetmc = MagicMock()
    mock_tsetmc_cls.return_value = mock_tsetmc
    sample_df = pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=50),
            "close": [1000.0] * 50,
            "high": [1050.0] * 50,
            "low": [950.0] * 50,
            "volume": [10000] * 50,
            "rsi": [55.0] * 50,
            "ema20": [990.0] * 50,
            "atr": [30.0] * 50,
        }
    )
    mock_tsetmc.fetch_symbol_data.return_value = {
        "symbol": "زهلال",
        "success": True,
        "history": sample_df,
        "client_type": {"buyer_power": 1.4},
    }

    mock_codal = MagicMock()
    mock_codal_cls.return_value = mock_codal
    mock_codal.fetch_codal_reports.return_value = {
        "symbol": "زهلال",
        "success": True,
        "letters_count": 5,
    }

    # Mock Validation
    mock_validate_all.return_value = ValidationResult(
        is_valid=True,
        candles_count=50,
        latest_close=1000.0,
        warnings=["Sample warning"],
        metrics_summary={"client_power": 1.4},
    )

    # Mock Technicals
    mock_calc_tech.return_value = sample_df
    mock_find_levels.return_value = {
        "swing_high": 1200.0,
        "swing_low": 800.0,
        "nearest_support": 950.0,
        "nearest_resistance": 1100.0,
    }
    mock_gen_charts.return_value = [
        tmp_path / "chart1.png",
        tmp_path / "chart2.png",
        tmp_path / "chart3.png",
    ]

    # Mock Fundamental & Recommendation
    mock_calc_fund.return_value = {
        "pe_ratio": 6.5,
        "ps_ratio": 1.2,
        "pb_ratio": 2.8,
        "dividend_yield_pct": 12.0,
        "fundamental_score": 7.5,
    }
    mock_gen_rec.return_value = {
        "overall_verdict": "خرید قوی (Strong Buy)",
        "action_desc": "موقعیت جذاب",
    }
    mock_gen_reports.return_value = {
        "fundamental": tmp_path / "fundamental_report.md",
        "technical": tmp_path / "technical_report.md",
        "recommendation": tmp_path / "final_recommendation.md",
    }

    result = main.analyze_symbol("زهلال", stocks_dir=tmp_path)

    assert result is True
    mock_tsetmc.fetch_symbol_data.assert_called_once_with("زهلال")
    mock_validate_all.assert_called_once()
    mock_calc_tech.assert_called_once()
    mock_find_levels.assert_called_once()
    mock_gen_charts.assert_called_once()
    mock_calc_fund.assert_called_once()
    mock_gen_rec.assert_called_once()
    mock_gen_reports.assert_called_once()


@patch("main.DataValidator.validate_all")
@patch("main.CodalFetcher")
@patch("main.TSETMCFetcher")
def test_analyze_symbol_validation_failure(
    mock_tsetmc_cls, mock_codal_cls, mock_validate_all, tmp_path
):
    mock_tsetmc = MagicMock()
    mock_tsetmc_cls.return_value = mock_tsetmc
    mock_tsetmc.fetch_symbol_data.return_value = {"success": False, "history": None}

    mock_validate_all.return_value = ValidationResult(
        is_valid=False,
        errors=["No price history available from TSETMC"],
    )

    result = main.analyze_symbol("نامعتبر", stocks_dir=tmp_path)

    assert result is False


@patch("main.analyze_symbol")
def test_main_cli_symbol(mock_analyze):
    mock_analyze.return_value = True
    main.main(["زهلال"])
    mock_analyze.assert_called_once_with("زهلال")


@patch("main.DirectoryWatcher.scan_and_process")
def test_main_cli_all(mock_scan):
    main.main(["--all"])
    mock_scan.assert_called_once_with(main.analyze_symbol)


@patch("main.DirectoryWatcher.watch_loop")
def test_main_cli_watch(mock_watch):
    main.main(["--watch"])
    mock_watch.assert_called_once_with(main.analyze_symbol)


@patch("main.DirectoryWatcher.scan_and_process")
def test_main_cli_default(mock_scan):
    main.main([])
    mock_scan.assert_called_once_with(main.analyze_symbol)
