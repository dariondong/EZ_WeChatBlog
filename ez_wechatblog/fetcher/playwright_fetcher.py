import logging

from ez_wechatblog.fetcher.base import BaseFetcher
from ez_wechatblog.fetcher.factory import FetcherFactory

logger = logging.getLogger(__name__)


@FetcherFactory.register("playwright")
class PlaywrightFetcher(BaseFetcher):
    def __init__(self, headless: bool = True, timeout: int = 30_000):
        self._headless = headless
        self._timeout = timeout
        self._playwright = None
        self._browser = None
        self._context = None

    async def _ensure_browser(self):
        if self._browser is not None:
            return
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ImportError(
                "playwright is not installed. Run: pip install 'ez-wechatblog[fetcher]'"
                " and then: playwright install chromium"
            )

        try:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self._headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                ],
            )
            self._context = await self._browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
                locale="zh-CN",
            )
        except Exception:
            await self._cleanup_partial()
            raise

    async def _cleanup_partial(self):
        if self._context:
            try:
                await self._context.close()
            except Exception:
                pass
            self._context = None
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
            self._browser = None
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

    async def fetch(self, url: str) -> str:
        await self._ensure_browser()
        page = await self._context.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=self._timeout)
            content = await page.content()
            return content
        finally:
            await page.close()

    async def close(self):
        if self._context:
            try:
                await self._context.close()
            except Exception:
                pass
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass