# Author: alimohammadzadeh@ut.ac.ir | Website: tjb24.ir
from pathlib import Path
import pytest
import re

def test_app_js_contains_4_zone_card_rendering():
    app_js = Path("browser/app.js").read_text(encoding="utf-8")

    assert "card-zone-header" in app_js
    assert "card-zone-hero" in app_js
    assert "ai-hero-pill" in app_js
    assert "card-zone-stats" in app_js
    assert "card-zone-actions" in app_js
    assert "quick-actions-menu" in app_js
    assert "openExplainabilityModal" in app_js


def test_app_js_contains_sparkline_and_pill_attributes():
    app_js = Path("browser/app.js").read_text(encoding="utf-8")

    # Zone 2 AI Hero Pill attributes
    assert 'data-action="open-xai"' in app_js
    assert 'data-pillar="overview"' in app_js
    assert "ai-hero-dots" in app_js or "ai-pill-dots" in app_js

    # Sparkline canvas and render function
    assert "sparkline-" in app_js
    assert "renderMiniSparkline" in app_js
    assert "renderStockChart" in app_js

    # Sparkline chart zero-axes configuration
    assert "display: false" in app_js


def test_app_js_contains_quick_actions_and_dropdown_wiring():
    app_js = Path("browser/app.js").read_text(encoding="utf-8")

    assert "btn-quick-actions" in app_js
    assert "btn-more-actions" in app_js
    assert "quick-actions-menu" in app_js
    assert "is-active" in app_js

    # Outside click closing listener
    assert "quick-actions-wrap" in app_js
    assert "_quickActionsOutsideListenerBound" in app_js or "document.addEventListener" in app_js


def test_app_js_preserves_critical_triggers():
    app_js = Path("browser/app.js").read_text(encoding="utf-8")

    assert "btn-live-avatar-trigger" in app_js
    assert "btn-summary" in app_js
    assert "favorite-btn" in app_js
    assert "btn-reanalyze" in app_js


def test_card_stats_strip_metrics():
    app_js = Path("browser/app.js").read_text(encoding="utf-8")

    # Zone 3 contains 4 metrics
    assert "ارزش بازار" in app_js
    assert "حجم" in app_js
    assert "P/E" in app_js
    assert "ورود/خروج پول" in app_js


def test_quick_actions_external_services():
    app_js = Path("browser/app.js").read_text(encoding="utf-8")

    # Zone 4 dropdown contains required external links
    assert "TSETMC" in app_js
    assert "رهاورد" in app_js
    assert "کدال" in app_js
    assert "گیت‌هاب" in app_js
