import pytest
from pathlib import Path
from ez_wechatblog.publishers.base import Article
from ez_wechatblog.publishers.hugo import HugoPublisher
from ez_wechatblog.publishers.hexo import HexoPublisher


class TestHugoPublisher:
    def test_get_name(self):
        pub = HugoPublisher()
        assert pub.get_name() == "hugo"

    def test_get_slug(self):
        article = Article(markdown="# Hi", metadata={"title": "My Article"})
        pub = HugoPublisher()
        assert pub.get_slug(article) == "my_article"

    def test_publish(self, tmp_path):
        pub = HugoPublisher()
        article = Article(
            markdown="---\ntitle: Test\n---\n\nHello",
            metadata={"title": "Test"},
        )
        result = pub.publish(article, {"output_dir": str(tmp_path)})
        md_path = Path(result["md_path"])
        assert md_path.exists()
        assert "content" in str(md_path) and "posts" in str(md_path)
        assert md_path.name == "index.md"
        assert md_path.read_text(encoding="utf-8").startswith("---")


class TestHexoPublisher:
    def test_get_name(self):
        pub = HexoPublisher()
        assert pub.get_name() == "hexo"

    def test_get_slug(self):
        article = Article(markdown="# Hi", metadata={"title": "My Article"})
        pub = HexoPublisher()
        assert pub.get_slug(article) == "My_Article"

    def test_publish(self, tmp_path):
        pub = HexoPublisher()
        article = Article(
            markdown="---\ntitle: Test\n---\n\nHello",
            metadata={"title": "Test"},
        )
        result = pub.publish(article, {"output_dir": str(tmp_path)})
        md_path = Path(result["md_path"])
        assert md_path.exists()
        assert "_posts" in str(md_path)
        assert md_path.name == "Test.md"
        assert md_path.read_text(encoding="utf-8").startswith("---")