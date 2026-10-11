# Author: alimohammadzadeh@ut.ac.ir | Website: tjb24.ir
from pathlib import Path
import re
import pytest

def test_styles_file_parity():
    s1 = Path("browser/styles.css").read_text(encoding="utf-8")
    s2 = Path("browser/style.css").read_text(encoding="utf-8")
    assert s1 == s2, "browser/styles.css and browser/style.css must be strictly identical"


def test_responsive_media_queries_exist():
    css = Path("browser/styles.css").read_text(encoding="utf-8")

    # Mobile breakpoint: max-width: 768px
    assert "@media (max-width: 768px)" in css, "Missing @media (max-width: 768px)"

    # Tablet breakpoint: min-width: 769px and max-width: 1023px
    assert "@media (min-width: 769px) and (max-width: 1023px)" in css, (
        "Missing @media (min-width: 769px) and (max-width: 1023px)"
    )

    # Desktop breakpoint: min-width: 1024px
    assert "@media (min-width: 1024px)" in css, "Missing @media (min-width: 1024px)"


def test_mobile_grid_card_height_and_overflow():
    css = Path("browser/styles.css").read_text(encoding="utf-8")

    # Find the mobile media query block
    match = re.search(r"@media\s*\(\s*max-width:\s*768px\s*\)\s*\{([\s\S]*?)\}\s*(?:@media|$)", css)
    assert match, "Could not extract @media (max-width: 768px) block"
    mobile_block = match.group(1)

    # 1fr grid for mobile
    assert "grid-template-columns: 1fr" in mobile_block, "Mobile grid must use 1fr"

    # Zero horizontal overflow
    assert "overflow-x: hidden" in mobile_block, "Mobile view must enforce overflow-x: hidden"

    # Compact card height (<200px)
    assert (
        "max-height: 200px" in mobile_block
        or "max-height: 198px" in mobile_block
        or "max-height: 195px" in mobile_block
    ), "Mobile stock card must enforce compact max-height < 200px"


def test_mobile_touch_targets():
    css = Path("browser/styles.css").read_text(encoding="utf-8")

    match = re.search(r"@media\s*\(\s*max-width:\s*768px\s*\)\s*\{([\s\S]*?)\}\s*(?:@media|$)", css)
    assert match, "Could not extract @media (max-width: 768px) block"
    mobile_block = match.group(1)

    # Minimum 44x44px touch targets for mobile buttons
    assert "favorite-btn" in mobile_block, "favorite-btn must be present in mobile media query"
    assert "btn-quick-actions" in mobile_block, "btn-quick-actions must be present in mobile media query"
    assert "btn-live-avatar" in mobile_block, "btn-live-avatar must be present in mobile media query"
    assert "btn-summary-minimal" in mobile_block, "btn-summary-minimal must be present in mobile media query"

    # Check that 44px min-height / min-width or 44px dimensions are enforced
    assert "44px" in mobile_block, "Mobile media query must enforce 44px touch targets"


def test_tablet_and_desktop_grid_breakpoints():
    css = Path("browser/styles.css").read_text(encoding="utf-8")

    # Tablet block: 2 columns
    match_tablet = re.search(
        r"@media\s*\(\s*min-width:\s*769px\s*\)\s*and\s*\(\s*max-width:\s*1023px\s*\)\s*\{([\s\S]*?)\}\s*(?:@media|$)",
        css,
    )
    assert match_tablet, "Could not extract tablet media query block"
    tablet_block = match_tablet.group(1)
    assert "repeat(2, 1fr)" in tablet_block, "Tablet grid must use repeat(2, 1fr)"

    # Desktop block: 3 columns
    match_desktop = re.search(r"@media\s*\(\s*min-width:\s*1024px\s*\)\s*\{([\s\S]*?)\}\s*(?:@media|$)", css)
    assert match_desktop, "Could not extract desktop media query block"
    desktop_block = match_desktop.group(1)
    assert "repeat(3, 1fr)" in desktop_block, "Desktop grid must use repeat(3, 1fr)"


def test_legacy_media_queries_do_not_bloat_stock_card():
    css = Path("browser/styles.css").read_text(encoding="utf-8")

    # Check max-width: 1180px and max-width: 992px
    # If .stock-card is present in these blocks, it must not bloat padding to 20px or gap to 20px/22px without scoping
    m_1180 = re.search(r"@media\s*\(\s*max-width:\s*1180px\s*\)\s*\{([\s\S]*?)\}", css)
    if m_1180:
        block_1180 = m_1180.group(1)
        # Plain unscoped .stock-card should NOT set grid-template-columns or 20px padding
        assert not re.search(r"(?<![.\-_a-zA-Z0-9])\.stock-card\s*\{[^}]*grid-template-columns", block_1180), (
            "Legacy media query (1180px) must not overwrite modern .stock-card layout"
        )

    m_992 = re.search(r"@media\s*\(\s*max-width:\s*992px\s*\)\s*\{([\s\S]*?)\}", css)
    if m_992:
        block_992 = m_992.group(1)
        assert not re.search(r"(?<![.\-_a-zA-Z0-9])\.stock-card\s*\{[^}]*gap:\s*22px", block_992), (
            "Legacy media query (992px) must not bloat .stock-card gap to 22px"
        )


def test_wcag_stat_label_contrast_color():
    css = Path("browser/styles.css").read_text(encoding="utf-8")

    # In Zone 3, .stat-label must have color #94a3b8 for WCAG contrast compliance
    match = re.search(r"\.card-zone-stats\s+\.stat-label\s*\{([\s\S]*?)\}", css)
    assert match, "Could not find .card-zone-stats .stat-label rule"
    rule = match.group(1)
    assert "#94a3b8" in rule, ".card-zone-stats .stat-label color must be bumped to #94a3b8"


def test_ai_hero_pill_keyboard_accessibility():
    app_js = Path("browser/app.js").read_text(encoding="utf-8")

    # app.js must handle keyboard interaction (Enter or Space) for .ai-hero-pill
    has_keyboard_xai = bool(
        re.search(r"ai-hero-pill[\s\S]{1,250}(?:Enter|' '|keyCode === 13|keyCode === 32)", app_js)
        or re.search(r"(?:Enter|' '|keyCode === 13|keyCode === 32)[\s\S]{1,250}ai-hero-pill", app_js)
    )
    assert has_keyboard_xai, "app.js must handle Enter/Space keyboard accessibility for .ai-hero-pill"

