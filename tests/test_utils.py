import pytest
from ez_wechatblog.utils import (
    sanitize_filename, extract_slug, get_ext_from_url,
    validate_url, is_valid_url, get_safe_filename,
)


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

    def test_no_false_positive(self):
        assert extract_slug("https://example.com/s/abc") is None


class TestGetExtFromUrl:
    def test_png(self):
        assert get_ext_from_url("https://example.com/image.png") == "png"

    def test_jpg(self):
        assert get_ext_from_url("https://example.com/photo.JPG?x=1") == "jpg"

    def test_no_ext(self):
        assert get_ext_from_url("https://example.com/photo") == "jpg"

    def test_webp(self):
        assert get_ext_from_url("https://example.com/img.webp?wx_fmt=webp") == "webp"


class TestValidateUrl:
    def test_valid_https(self):
        assert validate_url("https://mp.weixin.qq.com/s/xxx") == "https://mp.weixin.qq.com/s/xxx"

    def test_valid_http(self):
        assert validate_url("http://example.com") == "http://example.com"

    def test_strips_whitespace(self):
        assert validate_url("  https://example.com  ") == "https://example.com"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="不能为空"):
            validate_url("")

    def test_none_raises(self):
        with pytest.raises(ValueError):
            validate_url(None)

    def test_no_scheme_raises(self):
        with pytest.raises(ValueError, match="缺少协议"):
            validate_url("mp.weixin.qq.com/s/xxx")

    def test_ftp_raises(self):
        with pytest.raises(ValueError, match="不支持的协议"):
            validate_url("ftp://example.com")

    def test_no_netloc_raises(self):
        with pytest.raises(ValueError, match="格式无效"):
            validate_url("http://")


class TestIsValidUrl:
    def test_valid(self):
        assert is_valid_url("https://example.com") is True

    def test_invalid(self):
        assert is_valid_url("not a url") is False


class TestGetSafeFilename:
    def test_generates_unique_names(self):
        name1 = get_safe_filename("https://example.com/a.png", "png")
        name2 = get_safe_filename("https://example.com/a.png", "png")
        assert name1 != name2

    def test_preserves_extension(self):
        name = get_safe_filename("https://example.com/photo.jpg", "jpg")
        assert name.endswith(".jpg")

    def test_adds_extension_if_missing(self):
        name = get_safe_filename("https://example.com/image", "png")
        assert name.endswith(".png")