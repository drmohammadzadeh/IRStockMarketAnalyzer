# Author: alimohammadzadeh@ut.ac.ir | Website: tjb24.ir
from pathlib import Path
import re
import pytest

def test_styles_have_minimal_tokens_and_parity():
    s1 = Path("browser/styles.css").read_text(encoding="utf-8")
    s2 = Path("browser/style.css").read_text(encoding="utf-8")

    # Verify parity
    assert s1 == s2, "styles.css and style.css must be identical"

    # Verify key tokens and classes exist
    required_tokens = [
        "--bg-app",
        "--surface-card",
        "--surface-card-hover",
        "--border-subtle",
        "--color-ai-hero",
    ]
    for token in required_tokens:
        assert token in s1, f"Missing design token: {token}"

    required_classes = [
        ".card-zone-header",
        ".card-zone-hero",
        ".ai-hero-pill",
        ".card-zone-stats",
        ".card-zone-actions",
        ".quick-actions-menu",
    ]
    for cls in required_classes:
        assert cls in s1, f"Missing CSS class: {cls}"

def test_four_zone_components_and_dropdown_styles():
    s1 = Path("browser/styles.css").read_text(encoding="utf-8")

    additional_classes = [
        ".stock-card",
        ".sparkline-wrap",
        ".quick-actions-dropdown",
    ]
    for cls in additional_classes:
        assert cls in s1, f"Missing CSS class: {cls}"
