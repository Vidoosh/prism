"""Playwright-based fetch for JS-heavy sites."""

from __future__ import annotations

from typing import Optional

from playwright.async_api import async_playwright


async def playwright_fetch_html(url: str, timeout_ms: int = 30000) -> Optional[str]:
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            await page.wait_for_timeout(1500)
            html = await page.content()
            await browser.close()
            return html
    except Exception:
        return None
