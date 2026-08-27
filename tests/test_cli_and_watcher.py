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


@patch("main.MultiAgentOrchestrator")
def test_analyze_symbol_success(mock_orch_cls, tmp_path):
    mock_orch = MagicMock()
    mock_orch.run_pipeline.return_value = True
    mock_orch_cls.return_value = mock_orch

    result = main.analyze_symbol("زهلال", stocks_dir=tmp_path)

    assert result is True
    mock_orch_cls.assert_called_once_with(stocks_dir=tmp_path)
    mock_orch.run_pipeline.assert_called_once_with("زهلال", max_retries=3)


@patch("main.MultiAgentOrchestrator")
def test_analyze_symbol_validation_failure(mock_orch_cls, tmp_path):
    mock_orch = MagicMock()
    mock_orch.run_pipeline.return_value = False
    mock_orch_cls.return_value = mock_orch

    result = main.analyze_symbol("نامعتبر", stocks_dir=tmp_path)

    assert result is False
    mock_orch.run_pipeline.assert_called_once_with("نامعتبر", max_retries=3)


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
