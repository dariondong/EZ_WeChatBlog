import pytest
from pathlib import Path
from ez_wechatblog.templates.manager import TemplateManager, create_manager


SAMPLE_MD = "# Hello\n\nThis is **body** text."
SAMPLE_META = {"title": "Test", "author": "Me", "date": "2026-01-01",
               "tags": ["python", "blog"], "url": "https://example.com"}


class TestTemplateManager:
    def test_list_templates(self):
        tm = create_manager()
        templates = tm.list_templates()
        names = [t["name"] for t in templates]
        assert "markdown" in names
        assert "html" in names
        assert "frontmatter_full" in names
        assert "minimal" in names

    def test_render_markdown(self):
        tm = create_manager()
        result = tm.render("markdown.md.j2", SAMPLE_MD, SAMPLE_META,
                           front_matter="---\ntitle: Test\n---\n\n")
        assert "Hello" in result
        assert "Test" in result

    def test_render_html(self):
        tm = create_manager()
        result = tm.render("html.html.j2", SAMPLE_MD, SAMPLE_META)
        assert "<html" in result
        assert "<h1>Test</h1>" in result or "Test" in result
        assert "python" in result
        assert "blog" in result

    def test_render_frontmatter_full(self):
        tm = create_manager()
        result = tm.render("frontmatter_full.md.j2", SAMPLE_MD, SAMPLE_META)
        assert result.startswith("---")
        assert "title:" in result
        assert "author:" in result
        assert "tags:" in result

    def test_render_minimal(self):
        tm = create_manager()
        result = tm.render("minimal.md.j2", SAMPLE_MD, SAMPLE_META)
        assert "原文" in result
        assert SAMPLE_META["url"] in result

    def test_custom_template_dir(self, tmp_path):
        custom = tmp_path / "my_templates"
        custom.mkdir()
        tpl = custom / "custom.md.j2"
        tpl.write_text("---\ntitle: {{ metadata.title }}\n---\n\n{{ body }}", encoding="utf-8")
        tm = create_manager(custom_dirs=[custom])
        result = tm.render("custom.md.j2", SAMPLE_MD, SAMPLE_META)
        assert "title: Test" in result
        assert "body" in result

    def test_wrap_filter(self):
        tm = create_manager()
        assert tm._wrap_filter("hello") == '"hello"'

    def test_list_templates_shows_builtin_flag(self):
        tm = create_manager()
        for t in tm.list_templates():
            if t["name"] == "markdown":
                assert t["builtin"] is True
                break