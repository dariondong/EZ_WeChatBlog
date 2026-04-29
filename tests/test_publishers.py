import pytest
from pathlib import Path
from ez_wechatblog.publishers.base import Article
from ez_wechatblog.publishers.local import LocalPublisher
from ez_wechatblog.plugin_engine.manager import create_manager


class TestLocalPublisher:
    def test_get_name(self):
        pub = LocalPublisher()
        assert pub.get_name() == "local"

    def test_get_slug(self):
        article = Article(markdown="# Hi", metadata={"title": "My Article!"})
        pub = LocalPublisher()
        slug = pub.get_slug(article)
        assert slug == "My_Article"


class TestPluginManager:
    def test_create_manager(self):
        pm = create_manager()
        assert "local" in pm.list_publishers()

    def test_get_publisher(self):
        pm = create_manager()
        pub = pm.get_publisher("local")
        assert pub is not None
        assert pub.get_name() == "local"

    def test_get_publisher_unknown(self):
        pm = create_manager()
        assert pm.get_publisher("nonexistent") is None

    def test_publish_unknown(self):
        pm = create_manager()
        article = Article(markdown="test", metadata={})
        with pytest.raises(ValueError):
            pm.publish(article, "nonexistent")

    def test_publish_local(self, tmp_path):
        pm = create_manager()
        article = Article(
            markdown="---\ntitle: Test\n---\n\nHello",
            metadata={"title": "Test"},
        )
        result = pm.publish(article, "local", {
            "output_dir": str(tmp_path),
        })
        md_path = Path(result["md_path"])
        assert md_path.exists()
        assert md_path.read_text(encoding="utf-8") == "---\ntitle: Test\n---\n\nHello"