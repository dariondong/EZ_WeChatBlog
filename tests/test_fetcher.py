import pytest
from ez_wechatblog.fetcher.factory import FetcherFactory
from ez_wechatblog.fetcher.base import BaseFetcher
import ez_wechatblog.fetcher.playwright_fetcher  # noqa: register
import ez_wechatblog.fetcher.camoufox_fetcher  # noqa: register


class DummyFetcher(BaseFetcher):
    async def fetch(self, url: str) -> str:
        return ""

    async def close(self):
        pass


class TestFetcherFactory:
    def test_register_and_create(self):
        FetcherFactory.register("dummy_lc")(DummyFetcher)
        fetcher = FetcherFactory.create("dummy_lc")
        assert isinstance(fetcher, DummyFetcher)

    def test_create_unknown(self):
        with pytest.raises(ValueError, match="Unknown fetcher"):
            FetcherFactory.create("nonexistent")

    def test_playwright_registered(self):
        assert "playwright" in FetcherFactory._fetchers

    def test_camoufox_registered(self):
        assert "camoufox" in FetcherFactory._fetchers