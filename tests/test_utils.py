import pytest
from pathlib import Path
from ez_wechatblog.utils import sanitize_filename, extract_slug, get_ext_from_url


class TestSanitizeFilename:
    def test_basic(self):
        assert sanitize_filename("Hello World") == "Hello_World"

    def test_special_chars(self):
        assert sanitize_filename('a/b:c*d?e<f>g|h!') == "a_b_c_d_e_f_g_h"

    def test_max_length(self):
        long_name = "a" * 100
        assert len(sanitize_filename(long_name)) == 80

    def test_empty(self):
        assert sanitize_filename("") == "untitled"

    def test_trim_dots(self):
        result = sanitize_filename(".foo.")
        assert not result.startswith(".")
        assert not result.endswith(".")


class TestExtractSlug:
    def test_standard_url(self):
        url = "https://mp.weixin.qq.com/s/abc123DEF"
        assert extract_slug(url) == "abc123DEF"

    def test_with_params(self):
        url = "https://mp.weixin.qq.com/s/xyz789?param=val"
        assert extract_slug(url) == "xyz789"

    def test_no_match(self):
        assert extract_slug("https://example.com") is None


class TestGetExtFromUrl:
    def test_png(self):
        assert get_ext_from_url("https://example.com/image.png") == "png"

    def test_jpg(self):
        assert get_ext_from_url("https://example.com/photo.JPG?x=1") == "jpg"

    def test_no_ext(self):
        assert get_ext_from_url("https://example.com/photo") == "jpg"

    def test_webp(self):
        assert get_ext_from_url("https://example.com/img.webp?wx_fmt=webp") == "webp"