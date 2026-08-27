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

REQUIRED_SECTIONS = [
    "## نقش و هدف (Role & Objective)",
    "## ابزارها و ماژول‌ها (Tools & Capabilities)",
    "## ورودی‌ها (Inputs)",
    "## خروجی‌ها (Outputs)",
    "## سنجه‌های کیفی (Quality Rubric)",
    "## پرامپت سیستمی و دستورالعمل اجرایی (System Prompt & Execution Instructions)"
]

def test_all_agent_specs_exist():
    agents_dir = Path(__file__).resolve().parent.parent / ".agents"
    assert agents_dir.exists() and agents_dir.is_dir(), f"Agents directory does not exist: {agents_dir}"
    for name in AGENT_NAMES:
        spec_path = agents_dir / f"{name}.md"
        assert spec_path.exists(), f"Missing agent spec: {name}.md"
        content = spec_path.read_text(encoding="utf-8")
        for section in REQUIRED_SECTIONS:
            assert section in content, f"Missing section '{section}' in {name}.md"
