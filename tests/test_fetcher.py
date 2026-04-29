import pytest
from pathlib import Path

from ez_wechatblog.fetcher.factory import FetcherFactory
from ez_wechatblog.fetcher.base import BaseFetcher


class DummyFetcher(BaseFetcher):
    async def fetch(self, url: str) -> str:
        return f"<html><body><div id='js_content'><p>Content from {url}</p></div></body></html>"

    async def close(self):
        pass


class TestFetcherFactory:
    def test_register_and_create(self):
        FetcherFactory.register("dummy")(DummyFetcher)
        fetcher = FetcherFactory.create("dummy")
        assert isinstance(fetcher, DummyFetcher)

    def test_create_unknown(self):
        with pytest.raises(ValueError, match="Unknown fetcher"):
            FetcherFactory.create("nonexistent")

    def test_create_unknown_playwright(self):
        with pytest.raises(ValueError):
            FetcherFactory.create("playwright")