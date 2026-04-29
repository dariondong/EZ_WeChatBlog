import logging

from ez_wechatblog.fetcher.base import BaseFetcher
from ez_wechatblog.fetcher.factory import FetcherFactory

logger = logging.getLogger(__name__)


@FetcherFactory.register("camoufox")
class CamoufoxFetcher(BaseFetcher):
    def __init__(self, headless: bool = True, timeout: int = 30_000,
                 geoip: str | None = None, humanize: bool = True):
        self._headless = headless
        self._timeout = timeout
        self._geoip = geoip
        self._humanize = humanize
        self._camoufox = None
        self._browser = None

    async def _ensure_browser(self):
        if self._browser is not None:
            return
        try:
            from camoufox import AsyncCamoufox
        except ImportError:
            raise ImportError(
                "camoufox is not installed. Run: pip install camoufox"
                " and then: camoufox fetch"
            )

        kwargs = {
            "headless": self._headless,
            "humanize": self._humanize,
        }
        if self._geoip:
            kwargs["geoip"] = self._geoip

        try:
            self._camoufox = AsyncCamoufox(**kwargs)
            self._browser = await self._camoufox.start()
        except Exception:
            await self._cleanup_partial()
            raise

    async def _cleanup_partial(self):
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
            self._browser = None
        if self._camoufox:
            try:
                await self._camoufox.stop()
            except Exception:
                pass
            self._camoufox = None

    async def fetch(self, url: str) -> str:
        await self._ensure_browser()
        page = await self._browser.new_page()
        try:
            await page.goto(url, timeout=self._timeout)
            await page.wait_for_load_state("networkidle")
            content = await page.content()
            return content
        finally:
            await page.close()

    async def close(self):
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
        if self._camoufox:
            try:
                await self._camoufox.stop()
            except Exception:
                pass