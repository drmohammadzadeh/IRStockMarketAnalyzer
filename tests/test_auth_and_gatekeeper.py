# -*- coding: utf-8 -*-
"""
End-to-End Verification Test for User Registration, Activation, Forgot Password,
Analysis Requests Tracker, and Freemium Guest Gatekeeper (tjb24.ir).
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from src.auth_db import get_db_connection


def run_auth_and_gatekeeper_tests():
    print("=" * 70, flush=True)
    print("Starting Auth & Gatekeeper Headless Verification Tests...", flush=True)
    print("=" * 70, flush=True)

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-proxy-server")
    options.add_argument("--window-size=1400,900")
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 10)

    try:
        # ----------------------------------------------------------------------
        # TEST 1: Guest View & Freemium Gatekeeper
        # ----------------------------------------------------------------------
        print("\n[STEP 1] Testing Guest Access & Freemium Preview Gatekeeper...", flush=True)
        # Clear any local storage
        driver.get("http://127.0.0.1:8080/")
        driver.execute_script("localStorage.clear(); sessionStorage.clear();")
        driver.get("http://127.0.0.1:8080/")

        wait.until(EC.presence_of_element_located((By.ID, "stocksContainer")))
        time.sleep(2)

        # Verify Guest Preview Banner is visible
        guest_banner = driver.find_element(By.ID, "guestPreviewBanner")
        assert guest_banner.is_displayed(), "Guest Preview Banner should be visible for guest visitors!"
        banner_text = guest_banner.text
        assert "خودرو" in banner_text and "وتجارت" in banner_text and "کلید" in banner_text, "Banner should mention 3 preview symbols!"
        print("  ✓ Guest Preview Banner is clearly visible and mentions preview symbols.", flush=True)

        # Verify Guest Controls (Login & Register buttons in header)
        guest_controls = driver.find_element(By.ID, "guestHeaderControls")
        assert guest_controls.is_displayed(), "Guest header buttons must be visible for visitors!"
        user_menu = driver.find_element(By.ID, "userDropdownWrapper")
        assert not user_menu.is_displayed(), "User dropdown menu must be hidden for guests!"
        print("  ✓ Header displays Login and Register buttons for guest.", flush=True)

        # Verify Locked vs Unlocked Cards
        cards = driver.find_elements(By.CSS_SELECTOR, ".stock-card")
        assert len(cards) >= 12, f"Expected at least 12 cards, got {len(cards)}"

        preview_symbols = {"خودرو", "وتجارت", "کلید"}
        unlocked_count = 0
        locked_count = 0

        for card in cards:
            symbol = card.get_attribute("data-symbol")
            is_locked_class = "is-locked-stock" in (card.get_attribute("class") or "")
            overlays = card.find_elements(By.CSS_SELECTOR, ".locked-card-overlay")

            if symbol in preview_symbols:
                assert not is_locked_class, f"Preview symbol {symbol} should NOT be locked!"
                assert len(overlays) == 0, f"Preview symbol {symbol} should NOT have locked overlay!"
                unlocked_count += 1
            else:
                assert is_locked_class, f"Non-preview symbol {symbol} MUST be locked for guests!"
                assert len(overlays) == 1, f"Non-preview symbol {symbol} MUST have locked overlay!"
                locked_count += 1

        print(f"  ✓ Verified cards: {unlocked_count} preview stocks unlocked, {locked_count} stocks locked with overlay.", flush=True)

        # Test clicking locked card triggers Auth Modal
        first_locked = driver.find_element(By.CSS_SELECTOR, ".stock-card.is-locked-stock")
        first_locked.click()
        time.sleep(0.5)

        auth_modal = driver.find_element(By.ID, "authModal")
        assert auth_modal.is_displayed(), "Clicking a locked card should open Auth Modal!"
        print("  ✓ Clicking locked stock correctly triggers Auth Modal with prompt.", flush=True)

        # Close Auth Modal
        close_auth_btn = driver.find_element(By.ID, "closeAuthModalBtn")
        close_auth_btn.click()
        time.sleep(0.5)
        assert not auth_modal.is_displayed(), "Auth modal should close."

        # ----------------------------------------------------------------------
        # TEST 2: User Registration & Validation
        # ----------------------------------------------------------------------
        print("\n[STEP 2] Testing User Registration Flow...", flush=True)
        # Click Register button from header
        reg_header_btn = driver.find_element(By.ID, "openRegisterModalBtn")
        reg_header_btn.click()
        time.sleep(0.5)

        assert auth_modal.is_displayed(), "Auth modal should open upon clicking Register"
        reg_form = driver.find_element(By.ID, "registerForm")
        assert reg_form.is_displayed(), "Register form should be visible"

        # Test mobile number validation (must be 09xxxxxxxxx - 11 digits)
        test_ts = str(int(time.time()))[-7:]
        test_mobile = f"0912{test_ts}"
        test_email = f"test_{test_ts}@tjb24.ir"

        driver.find_element(By.ID, "regFirstName").send_keys("مهدی")
        driver.find_element(By.ID, "regLastName").send_keys("رضایی")
        driver.find_element(By.ID, "regMobile").send_keys("08123456789")  # Invalid: does not start with 09
        driver.find_element(By.ID, "regEmail").send_keys(test_email)
        driver.find_element(By.ID, "regPassword").send_keys("securePass123")
        driver.find_element(By.ID, "regPasswordConfirm").send_keys("securePass123")

        submit_reg_btn = driver.find_element(By.ID, "submitRegisterBtn")
        submit_reg_btn.click()
        time.sleep(0.5)

        alert_box = driver.find_element(By.ID, "authAlertBox")
        assert alert_box.is_displayed() and "۰۹" in alert_box.text, "Invalid mobile number must be rejected!"
        print("  ✓ Rejected invalid mobile number (must start with 09).", flush=True)

        # Now enter valid 09 mobile number (11 digits)
        mob_input = driver.find_element(By.ID, "regMobile")
        mob_input.clear()
        mob_input.send_keys(test_mobile)

        submit_reg_btn.click()
        time.sleep(1.0)

        # Modal should transition to activation form
        act_form = driver.find_element(By.ID, "activateForm")
        assert act_form.is_displayed(), "Registration success should transition to activate form!"
        print(f"  ✓ User registered with mobile {test_mobile}. Form transitioned to Activation.", flush=True)

        # Retrieve activation code from SQLite DB
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT ua.activation_code, ua.activation_token 
            FROM user_activations ua
            JOIN users u ON u.id = ua.user_id
            WHERE u.mobile = ?
            ORDER BY ua.id DESC LIMIT 1
        """, (test_mobile,))
        act_rec = cur.fetchone()
        conn.close()

        assert act_rec is not None, "Activation record must exist in DB!"
        act_code = act_rec["activation_code"]
        act_token = act_rec["activation_token"]
        print(f"  ✓ Retrieved 6-digit activation code: {act_code}", flush=True)

        # ----------------------------------------------------------------------
        # TEST 3: Account Activation & Freemium Unlock
        # ----------------------------------------------------------------------
        print("\n[STEP 3] Testing Account Activation via 6-digit Code...", flush=True)
        act_code_input = driver.find_element(By.ID, "actCode")
        act_code_input.clear()
        act_code_input.send_keys(act_code)

        submit_act_btn = driver.find_element(By.ID, "submitActivateBtn")
        submit_act_btn.click()
        time.sleep(1.5)

        # Modal should close and user is logged in
        assert not auth_modal.is_displayed(), "Auth modal should close after successful activation"
        user_menu = driver.find_element(By.ID, "userDropdownWrapper")
        assert user_menu.is_displayed(), "User dropdown menu should now be visible!"
        user_name_label = driver.find_element(By.ID, "userNameLabel").text
        assert "مهدی" in user_name_label, f"User name label should show user name, got: {user_name_label}"
        print(f"  ✓ User successfully logged in as: {user_name_label}", flush=True)

        # Verify Guest Preview Banner is HIDDEN for logged-in users
        guest_banner = driver.find_element(By.ID, "guestPreviewBanner")
        assert not guest_banner.is_displayed(), "Guest banner must be hidden when user is logged in!"
        print("  ✓ Guest Preview Banner is hidden for authenticated member.", flush=True)

        # Verify ALL 17 stocks are now UNLOCKED
        cards_after_login = driver.find_elements(By.CSS_SELECTOR, ".stock-card")
        locked_after_login = driver.find_elements(By.CSS_SELECTOR, ".stock-card.is-locked-stock")
        assert len(locked_after_login) == 0, f"ALL cards must be unlocked after login! Found {len(locked_after_login)} locked."
        print(f"  ✓ ALL {len(cards_after_login)} stock cards are 100% UNLOCKED and accessible!", flush=True)

        # ----------------------------------------------------------------------
        # TEST 4: User Stock Analysis Requests Tracking
        # ----------------------------------------------------------------------
        print("\n[STEP 4] Testing User Stock Analysis Requests Tracker...", flush=True)
        # Open User Profile Menu
        user_prof_btn = driver.find_element(By.ID, "userProfileBtn")
        user_prof_btn.click()
        time.sleep(0.5)

        # Click "درخواست‌های تحلیل من"
        open_requests_btn = driver.find_element(By.ID, "openMyRequestsBtn")
        open_requests_btn.click()
        time.sleep(1.0)

        req_modal = driver.find_element(By.ID, "myRequestsModal")
        assert req_modal.is_displayed(), "My Requests modal should open!"
        print("  ✓ My Requests modal opened successfully.", flush=True)

        # Submit a new analysis request
        add_req_btn = driver.find_element(By.ID, "modalAddNewRequestBtn")
        add_req_btn.click()
        time.sleep(0.5)

        add_stock_modal = driver.find_element(By.ID, "addStockModal")
        assert add_stock_modal.is_displayed(), "Add stock modal should open"

        # Check name and email were auto-prefilled
        name_val = driver.find_element(By.ID, "applicantName").get_attribute("value")
        email_val = driver.find_element(By.ID, "applicantEmail").get_attribute("value")
        assert "مهدی" in name_val, "Applicant name should be prefilled with user name"
        print(f"  ✓ Add Stock form auto-prefilled user identity: {name_val} ({email_val})", flush=True)

        driver.find_element(By.ID, "requestedSymbol").send_keys("فولاد مبارکه اصفهان")
        # Select request type
        from selenium.webdriver.support.ui import Select
        req_type_select = Select(driver.find_element(By.ID, "requestType"))
        req_type_select.select_by_value("1")

        submit_add_btn = driver.find_element(By.ID, "submitAddStockBtn")
        submit_add_btn.click()
        time.sleep(1.5)

        print("  ✓ Submitted new stock analysis request for 'فولاد'.", flush=True)

        # Reopen My Requests modal to see the new request listed
        user_prof_btn.click()
        time.sleep(0.5)
        open_requests_btn.click()
        time.sleep(1.0)

        req_rows = driver.find_elements(By.CSS_SELECTOR, "#myRequestsTableBody tr")
        assert len(req_rows) >= 1, "Submitted request must appear in My Requests table!"
        table_text = driver.find_element(By.ID, "myRequestsTableBody").text
        assert "فولاد" in table_text, "Requested symbol 'فولاد' must be in table!"
        assert "در صف بررسی" in table_text, "Status 'در صف بررسی' must be in table!"
        print(f"  ✓ My Requests table correctly displays submitted request for 'فولاد' with status 'در صف بررسی'.", flush=True)

        # Close My Requests modal
        driver.find_element(By.ID, "closeMyRequestsModalBtn").click()
        time.sleep(0.5)

        # ----------------------------------------------------------------------
        # TEST 5: Logout & Re-locking Verification
        # ----------------------------------------------------------------------
        print("\n[STEP 5] Testing Logout & Re-locking...", flush=True)
        user_prof_btn.click()
        time.sleep(0.5)
        driver.find_element(By.ID, "userLogoutBtn").click()
        time.sleep(1.0)

        # After logout:
        guest_banner = driver.find_element(By.ID, "guestPreviewBanner")
        assert guest_banner.is_displayed(), "Guest banner must reappear after logout"
        user_menu = driver.find_element(By.ID, "userDropdownWrapper")
        assert not user_menu.is_displayed(), "User dropdown menu must hide after logout"

        cards_after_logout = driver.find_elements(By.CSS_SELECTOR, ".stock-card.is-locked-stock")
        assert len(cards_after_logout) > 0, "Non-preview stock cards must be re-locked after logout!"
        print(f"  ✓ User logged out cleanly. {len(cards_after_logout)} stock cards re-locked for guests.", flush=True)

        print("\n" + "=" * 70)
        print("ALL AUTH, REQUESTS TRACKING, AND GATEKEEPER TESTS PASSED WITH 100% SUCCESS!", flush=True)
        print("=" * 70)

    finally:
        driver.quit()


if __name__ == "__main__":
    run_auth_and_gatekeeper_tests()
