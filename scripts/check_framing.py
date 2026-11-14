"""Render the standalone store and check its frame, navigation and main dialogs.

Run a built preview server first. Requires Playwright and an installed Chrome
on Windows (or the Playwright Chromium browser on other platforms).
"""
from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
WIDTHS = (320, 390, 768, 1024, 1280, 1440, 1920)


def run(url: str):
    output = ROOT / "artifacts" / "framing"
    output.mkdir(parents=True, exist_ok=True)
    report = {"viewports": [], "browser": "", "flows": []}
    with sync_playwright() as playwright:
        options = {"channel": "chrome"} if platform.system() == "Windows" else {}
        browser = playwright.chromium.launch(headless=True, **options)
        report["browser"] = browser.version
        for width in WIDTHS:
            context = browser.new_context(viewport={"width": width, "height": 900}, service_workers="block")
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(url)
            page.locator(".product-card").first.wait_for()
            page.evaluate("document.fonts.ready")
            metrics = page.evaluate("""() => {
              const box = selector => { const r = document.querySelector(selector).getBoundingClientRect();
                return {x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,bottom:r.bottom}; };
              return {overflow:document.documentElement.scrollWidth-innerWidth,
                frame:box('.studio-frame'),dock:box('.studio-dock'),hero:box('.hero'),
                shortlist:box('.studio-shortlist'),title:box('.hero h1')};
            }""")
            assert metrics["overflow"] <= 0, (width, metrics)
            assert metrics["frame"]["right"] <= width + 1, (width, metrics)
            assert metrics["title"]["height"] < 125, (width, metrics)
            overlaps = page.locator(".site-header").evaluate("""header => {
              const boxes = [...header.children].filter(e => getComputedStyle(e).display !== 'none').map(e => e.getBoundingClientRect());
              return boxes.some((a,i) => boxes.slice(i+1).some(b => Math.min(a.right,b.right)-Math.max(a.left,b.left)>2 && Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>2));
            }""")
            assert not overlaps, (width, "header controls overlap")
            if width > 760:
                assert metrics["dock"]["right"] + 8 <= metrics["frame"]["x"], (width, metrics)
            else:
                assert metrics["dock"]["bottom"] <= 900, (width, metrics)
            if 760 < width <= 1100:
                assert metrics["shortlist"]["y"] >= metrics["hero"]["bottom"], (width, metrics)
            page.screenshot(path=str(output / f"music-{width}.png"))

            page.locator("[data-glass-open]").click()
            dialog = page.locator("#glass-settings-dialog")
            bounds = dialog.bounding_box()
            assert bounds and 0 <= bounds["x"] and bounds["x"] + bounds["width"] <= width + 1
            page.screenshot(path=str(output / f"settings-{width}.png"))
            page.locator('[data-glass-palette="cobalt"]').click()
            page.locator("#glass-opacity").evaluate("e => {e.value='20';e.dispatchEvent(new Event('input',{bubbles:true}));}")
            page.reload()
            page.locator("[data-glass-open]").click()
            assert page.locator("#glass-opacity").input_value() == "20"
            page.locator("#glass-reset").click()
            assert page.locator("body").get_attribute("data-glass-material") == "false"
            page.locator(".glass-settings-close").click()

            if width == 1280:
                page.locator(".compare-check").nth(0).click()
                page.locator(".compare-check").nth(1).click()
                page.locator("#compare-open").click()
                page.locator("#compare-dialog[open]").wait_for()
                assert page.locator(".comparison-table").count() == 1
                page.locator('[data-close="compare-dialog"]').click()
                page.locator(".add-small:not([disabled])").first.click()
                page.wait_for_function("Number(document.querySelector('#bag-count').textContent) > 0")
                page.locator("#bag-button").click()
                page.locator("#cart-dialog[open]").wait_for()
                page.locator("#checkout-button").click()
                page.locator("#checkout-dialog[open]").wait_for()
                assert page.locator("#checkout-content").inner_text()
                report["flows"].extend(["comparison", "bag", "checkout_preview"])

            page.goto(url.rstrip("/") + "/sound-lab/")
            page.locator("#piano button").first.wait_for()
            page.evaluate("document.fonts.ready")
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (width, "sound overflow")
            page.screenshot(path=str(output / f"sound-{width}.png"))
            if width == 1280:
                page.locator("#play-chord").click()
                page.wait_for_function("document.querySelector('#audio-state').textContent.includes('Generated chord')")
                page.locator("#stop-audio").click()
                assert page.locator("#signal-source").inner_text() == "OFF"
                report["flows"].append("chord_synthesis_and_stop")
            assert not errors, (width, errors)
            report["viewports"].append({"width": width, "height": 900, "overflow": metrics["overflow"], "title_height": metrics["title"]["height"], "status": "PASS"})
            context.close()
        browser.close()
    report["flows"].extend(["settings_open", "palette", "opacity_persistence", "restore_original", "sound_lab_framing"])
    report["status"] = "PASS"
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8765/")
    run(parser.parse_args().url)
