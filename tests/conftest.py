import pytest
from pathlib import Path

@pytest.fixture
def sample_stocks_dir(tmp_path):
    d = tmp_path / "سهام"
    d.mkdir()
    symbol_dir = d / "زهلال"
    symbol_dir.mkdir()
    (symbol_dir / "links.txt").write_text("https://codal.ir/ReportList.aspx?search&Symbol=%D8%B2%D9%87%D9%84%D8%A7%D9%84", encoding="utf-8")
    return d
