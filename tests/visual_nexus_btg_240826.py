"""QA visual local do dossiê BTG/Nexus de 24/08/2026."""

import json
from pathlib import Path

from playwright.sync_api import sync_playwright


URL = "http://127.0.0.1:8765/nexus_btg_240826.html"
OUTPUT = Path("/tmp/nexus-btg-240826-qa")


def inspect(page, name: str) -> dict:
    page.goto(URL, wait_until="networkidle")
    page.screenshot(path=str(OUTPUT / f"{name}-top.png"))
    for node in page.locator(".reveal").all():
        node.scroll_into_view_if_needed()
        page.wait_for_timeout(35)
    if name == "desktop":
        for index, figure in enumerate(page.locator("figure.figure").all(), start=1):
            figure.screenshot(path=str(OUTPUT / f"figure-{index}.png"))
    page.locator("#veredito").scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    page.screenshot(path=str(OUTPUT / f"{name}-full.png"), full_page=True)
    page.locator(".hero").screenshot(path=str(OUTPUT / f"{name}-hero.png"))
    return page.evaluate(
        """() => ({
          title: document.title,
          sections: document.querySelectorAll('main section').length,
          figures: document.querySelectorAll('.canvas svg').length,
          hiddenReveals: [...document.querySelectorAll('.reveal')]
            .filter(node => getComputedStyle(node).opacity === '0').length,
          horizontalOverflow: document.documentElement.scrollWidth - innerWidth,
          activeNav: document.querySelectorAll('.toc a.active').length,
          cardImage: document.querySelector('meta[property="og:image"]').content,
          activeElement: document.activeElement && document.activeElement.tagName,
        })"""
    )


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    console_errors = []
    failed_requests = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
        desktop.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        desktop.on("requestfailed", lambda request: failed_requests.append(request.url))
        desktop_result = inspect(desktop, "desktop")

        mobile = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=1)
        mobile.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        mobile.on("requestfailed", lambda request: failed_requests.append(request.url))
        mobile_result = inspect(mobile, "mobile")
        browser.close()

    result = {
        "desktop": desktop_result,
        "mobile": mobile_result,
        "console_errors": console_errors,
        "failed_requests": failed_requests,
        "screenshots": str(OUTPUT),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

    for view in (desktop_result, mobile_result):
        assert view["sections"] == 13
        assert view["figures"] == 6
        assert view["hiddenReveals"] == 0
        assert view["horizontalOverflow"] <= 1
        assert view["activeNav"] == 1
    assert not console_errors


if __name__ == "__main__":
    main()
