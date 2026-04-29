WEIXIN_SAMPLE = """<!DOCTYPE html>
<html>
<head>
  <meta property="og:title" content="Python 进阶指南" />
  <title>Python 进阶指南</title>
  <meta property="og:description" content="作者：张三" />
  <style>.rich_media_content{overflow:hidden}</style>
</head>
<body>
  <div id="js_content">
    <section style="padding:10px;">
      <p>这是一篇关于 Python 进阶的文章。</p>
      <section>
        <p>下面是一段代码：</p>
      </section>
      <code-snippet data-lang="python">
def hello():
    print("world")
</code-snippet>
      <p> </p>
      <section style="margin:10px;">
        <img data-src="https://mmbiz.qpic.cn/abc.png?wx_fmt=png" data-w="800" />
      </section>
      <mpvideo data-vid="VID12345"></mpvideo>
      <mpvoice data-name="语音讲解"></mpvoice>
      <p data-tools="markdown" data-id="123">一些内容</p>
    </section>
    <p>结尾段落。</p>
  </div>
</body>
</html>"""


def test_parse_realistic_sample():
    from ez_wechatblog.parser.wechat_parser import WeChatParser
    parser = WeChatParser()
    body, meta, images, raw_html = parser.parse(WEIXIN_SAMPLE, url="https://mp.weixin.qq.com/s/test123")

    assert meta.title == "Python 进阶指南"
    assert "张三" in meta.author or not meta.author
    assert "Python" in body
    assert "print" in body or "hello" in body or "world" in body
    assert len(images) >= 1
    assert "<div" in raw_html or "<p" in raw_html


def test_inline_style_removed():
    from bs4 import BeautifulSoup
    from ez_wechatblog.parser.cleaners.generic import clean_inline_styles
    soup = BeautifulSoup('<div style="color:red;"><p style="margin:0">text</p></div>', "html.parser")
    clean_inline_styles(soup)
    assert "style" not in soup.find("div").attrs
    assert "style" not in soup.find("p").attrs


def test_empty_tags_removed():
    from bs4 import BeautifulSoup
    from ez_wechatblog.parser.cleaners.generic import clean_empty_tags
    soup = BeautifulSoup("<p> </p><p>text</p><p></p><img src='x.png'/>", "html.parser")
    clean_empty_tags(soup)
    ps = soup.find_all("p")
    assert len(ps) == 1
    assert ps[0].get_text(strip=True) == "text"


def test_section_unwrapped():
    from bs4 import BeautifulSoup
    from ez_wechatblog.parser.cleaners.generic import clean_section_tags
    soup = BeautifulSoup("<section><p>hello</p></section>", "html.parser")
    clean_section_tags(soup)
    assert not soup.find("section")
    assert soup.find("p").get_text(strip=True) == "hello"


def test_data_attrs_removed():
    from bs4 import BeautifulSoup
    from ez_wechatblog.parser.cleaners.generic import clean_data_attrs
    soup = BeautifulSoup('<p data-tools="markdown" data-id="123">text</p>', "html.parser")
    clean_data_attrs(soup)
    p = soup.find("p")
    assert "data-tools" not in p.attrs
    assert "data-id" not in p.attrs


def test_style_script_decomposed():
    from bs4 import BeautifulSoup
    from ez_wechatblog.parser.cleaners.generic import clean_inline_styles
    soup = BeautifulSoup("<div><style>.x{}</style><script>alert()</script><p>text</p></div>", "html.parser")
    clean_inline_styles(soup)
    assert not soup.find("style")
    assert not soup.find("script")
    assert soup.find("p").get_text(strip=True) == "text"


def test_full_clean_pipeline():
    from bs4 import BeautifulSoup
    from ez_wechatblog.parser.cleaners.generic import full_clean
    html = """
    <div>
      <section style="color:red;">
        <p data-tools="x" data-id="1"> </p>
        <p>valid</p>
      </section>
      <style>.x{}</style>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")
    full_clean(soup)
    assert not soup.find("section")
    assert not soup.find("style")
    ps = soup.find_all("p")
    assert len(ps) == 1
    assert ps[0].get_text(strip=True) == "valid"