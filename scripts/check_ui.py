"""Historical 1.0 UI check; not valid for KONAET Music 2.0.

Current event contracts are in tests/ui/interface.test.mjs. A new browser/device
review is required before claiming visual or microphone QA for the redesign.
"""
from __future__ import annotations

import json
import platform
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent


def main():
    target = ROOT / "docs" / "screenshots"
    target.mkdir(parents=True, exist_ok=True)
    errors = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, **({"channel": "chrome"} if platform.system() == "Windows" else {}))
        context = browser.new_context(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto("http://127.0.0.1:8000")
        page.get_by_text("Your music desk is ready").wait_for()
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        page.screenshot(path=str(target / "desktop.png"), full_page=True)
        page.locator(".prompt").first.click()
        page.locator(".message.assistant").first.wait_for()
        assert "BRL" in page.locator(".message.assistant").first.inner_text()
        page.screenshot(path=str(target / "conversation.png"), full_page=True)
        page.get_by_role("button", name="Explore instruments").click()
        page.locator(".product-card").first.wait_for()
        assert page.locator(".product-card").count() > 0
        page.get_by_role("button", name="Store information").click()
        page.locator("#policy-list summary").first.wait_for()
        assert page.locator("#policy-list details").count() == 9
        page.get_by_role("button", name="Verify order", exact=False).click()
        page.locator("#order-id").fill("8")
        page.locator("#purchase-email").fill("anacarol.ferreira@coldmail.com")
        page.get_by_role("button", name="Verify securely").click()
        page.get_by_text("Order verified ✓").wait_for()
        page.get_by_text("Tracking code: BRJL5544332BR.", exact=False).wait_for()
        page.get_by_role("button", name="New conversation").click()
        page.locator("#welcome").wait_for(state="visible")
        assert page.locator(".message").count() == 0
        mobile_context = browser.new_context(viewport={"width": 375, "height": 812}, is_mobile=True, device_scale_factor=1)
        mobile = mobile_context.new_page()
        mobile.on("pageerror", lambda error: errors.append(str(error)))
        mobile.goto("http://127.0.0.1:8000")
        mobile.get_by_text("Your music desk is ready").wait_for()
        assert mobile.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        assert mobile.locator("#new-chat").is_visible()
        mobile.screenshot(path=str(target / "mobile.png"), full_page=True)
        mobile.locator("#language-select").select_option("pt")
        mobile.get_by_text("Seu atendimento está pronto").wait_for()
        assert mobile.locator("html").get_attribute("lang") == "pt-BR"
        assert mobile.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        mobile.screenshot(path=str(target / "portuguese.png"), full_page=True)
        mobile.locator(".prompt").nth(1).click()
        mobile.get_by_text("R$ 2.199,00", exact=False).wait_for(timeout=60000)
        browser.close()
    assert not errors, errors
    report = {"status": "PASS", "desktop": "1440x1000", "mobile": "375x812", "javascript_errors": errors,
              "checks": ["initial readiness", "catalog-grounded chat", "catalog view", "policy view", "order verification",
                         "verified order status", "session reset", "no horizontal overflow", "mobile new conversation", "Portuguese interface and answer"]}
    (ROOT / "docs" / "ui-check.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
