import pytest
from bs4 import BeautifulSoup

from ez_wechatblog.parser.wechat_parser import WeChatParser, ArticleMeta


SAMPLE_HTML = """<!DOCTYPE html>
<html>
<head>
  <meta property="og:title" content="测试文章标题" />
  <title>测试文章标题</title>
</head>
<body>
  <div id="js_content">
    <p>这是一段测试正文。</p>
    <p>这是第二段。</p>
    <img data-src="https://mmbiz.qpic.cn/example.png" />
    <code-snippet data-lang="python">
print("hello")
</code-snippet>
  </div>
</body>
</html>"""


def test_parse_basic():
    parser = WeChatParser()
    body, meta, images = parser.parse(SAMPLE_HTML, url="https://mp.weixin.qq.com/s/test")

    assert meta.title == "测试文章标题"
    assert "这是一段测试正文" in body
    assert "print(" in body or "hello" in body


def test_parse_no_content():
    parser = WeChatParser()
    with pytest.raises(ValueError):
        parser.parse("<html><body><p>no content</p></body></html>")


def test_article_meta_to_dict():
    meta = ArticleMeta(title="T", author="A", date="2024-01-01",
                       tags=["tech"], url="https://example.com")
    d = meta.to_dict()
    assert d["title"] == "T"
    assert d["author"] == "A"
    assert d["tags"] == ["tech"]


def test_build_full_markdown():
    parser = WeChatParser()
    meta = ArticleMeta(title="测试", author="作者", url="https://mp.weixin.qq.com/s/x")
    result = parser.build_full_markdown("正文内容", meta)
    assert result.startswith("---")
    assert "title: 测试" in result
    assert "正文内容" in result


def test_extract_images():
    parser = WeChatParser()
    _, _, images = parser.parse(SAMPLE_HTML)
    assert len(images) == 1
    assert "example.png" in images[0]


def test_image_cleanup():
    html = """<html><body><div id="js_content">
    <img data-src="https://example.com/a.png" />
    <img src="https://example.com/b.png" />
    <img src="data:image/png;base64,abc" />
    <img />
    </div></body></html>"""
    parser = WeChatParser()
    _, _, images = parser.parse(html)
    assert len(images) == 2
    assert "a.png" in images[0]