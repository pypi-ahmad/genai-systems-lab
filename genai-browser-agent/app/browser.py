from __future__ import annotations

from playwright.sync_api import sync_playwright, Browser, Page, Locator


class BrowserController:
    def __init__(self, headless: bool = True) -> None:
        self._playwright = sync_playwright().start()
        self._browser: Browser = self._playwright.chromium.launch(headless=headless)
        self._page: Page = self._browser.new_page()

    def open_url(self, url: str) -> None:
        self._page.goto(url, wait_until="domcontentloaded")

    def get_page_text(self) -> str:
        return self._page.inner_text("body")

    def click(self, target: str) -> None:
        locator = self._resolve_clickable(target)
        locator.click()

    def type(self, target: str, text: str) -> None:
        locator = self._resolve_input(target)
        locator.fill(text)

    def close(self) -> None:
        self._browser.close()
        self._playwright.stop()

    def screenshot(self) -> bytes:
        return self._page.screenshot(type="png")

    # ------------------------------------------------------------------
    # Element resolution helpers
    # ------------------------------------------------------------------

    def _first_visible(self, locator: Locator) -> Locator | None:
        if locator.count() > 0 and locator.first.is_visible():
            return locator.first
        return None

    def _resolve_clickable(self, target: str) -> Locator:
        page = self._page

        for locator in (
            page.get_by_role("link", name=target),
            page.get_by_role("button", name=target),
            page.get_by_text(target, exact=False),
        ):
            found = self._first_visible(locator)
            if found is not None:
                return found

        return page.locator(target).first

    def _resolve_input(self, target: str) -> Locator:
        page = self._page

        for locator in (
            page.get_by_label(target),
            page.get_by_placeholder(target),
            page.get_by_role("textbox", name=target),
            page.get_by_role("searchbox", name=target),
        ):
            found = self._first_visible(locator)
            if found is not None:
                return found

        return page.locator(target).first