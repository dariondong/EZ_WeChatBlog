import pytest
from pathlib import Path
from ez_wechatblog.assets.manager import (
    AssetManager, HOST_REGISTRY, GitHubImageHost, OSSImageHost,
    CloudinaryImageHost, build_host_config,
)


class TestAssetManagerLocal:
    def test_init_creates_dir(self, tmp_path):
        am = AssetManager(tmp_path, assets_subdir="myimages")
        assert am.assets_dir.exists()
        assert am.assets_dir.name == "myimages"

    async def test_empty_download(self, tmp_path):
        am = AssetManager(tmp_path)
        results = await am.download_all([])
        assert results == []

    def test_rewrite_no_mapping(self, tmp_path):
        am = AssetManager(tmp_path)
        md = "![alt](https://example.com/img.png)"
        result = am.rewrite_markdown_images(md)
        assert result == md

    def test_rewrite_with_mapping(self, tmp_path):
        am = AssetManager(tmp_path)
        am._mapping = {"https://example.com/a.png": "images/a.png"}
        md = "![alt](https://example.com/a.png)"
        result = am.rewrite_markdown_images(md)
        assert result == "![alt](images/a.png)"

    def test_rewrite_fuzzy_match(self, tmp_path):
        am = AssetManager(tmp_path)
        am._mapping = {"https://mmbiz.qpic.cn/sz_mmbiz_png/abc/123.png?wx_fmt=png": "images/123.png"}
        md = "![pic](https://mmbiz.qpic.cn/sz_mmbiz_png/abc/123.png?wx_fmt=png)"
        result = am.rewrite_markdown_images(md)
        assert "images/123.png" in result

    async def test_download_bad_url(self, tmp_path):
        am = AssetManager(tmp_path)
        results = await am.download_all(["https://nonexistent.example.com/img.png"])
        assert results == []

    def test_concurrent_limit(self, tmp_path):
        am = AssetManager(tmp_path, max_concurrent=2)
        assert am.semaphore._value == 2


class TestAssetManagerBase64:
    def test_base64_mode(self, tmp_path):
        am = AssetManager(tmp_path, image_mode="base64")
        assert am.image_mode == "base64"

    async def test_store_base64(self, tmp_path):
        am = AssetManager(tmp_path, image_mode="base64")
        data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 10
        result = await am._store_image(data, "test.png", "https://example.com/test.png")
        assert result[0] == ""
        assert result[1].startswith("data:image/png;base64,")


class TestAssetManagerRemote:
    def test_remote_no_host_raises(self, tmp_path):
        am = AssetManager(tmp_path, image_mode="remote")
        with pytest.raises(RuntimeError, match="No image host configured"):
            import asyncio
            asyncio.run(am._store_image(b"data", "test.png", "https://example.com/test.png"))

    def test_remote_with_host(self, tmp_path):
        host = GitHubImageHost(repo="user/repo", token="fake")
        am = AssetManager(tmp_path, image_mode="remote", image_host=host)
        assert am.image_host.get_name() == "github"


class TestOSSImageHost:
    def test_name(self):
        host = OSSImageHost(endpoint="oss-cn-hangzhou.aliyuncs.com",
                            bucket="b", access_key="ak", secret_key="sk")
        assert host.get_name() == "oss"

    def test_required_config(self):
        assert "endpoint" in OSSImageHost.required_config()
        assert "bucket" in OSSImageHost.required_config()
        assert "access_key" in OSSImageHost.required_config()
        assert "secret_key" in OSSImageHost.required_config()

    def test_optional_config(self):
        assert "path_prefix" in OSSImageHost.optional_config()

    def test_guess_content_type(self):
        assert OSSImageHost._guess_content_type("a.png") == "image/png"
        assert OSSImageHost._guess_content_type("a.jpg") == "image/jpeg"
        assert OSSImageHost._guess_content_type("a.gif") == "image/gif"
        assert OSSImageHost._guess_content_type("a.webp") == "image/webp"
        assert OSSImageHost._guess_content_type("a.xyz") == "application/octet-stream"


class TestGitHubImageHost:
    def test_name(self):
        host = GitHubImageHost(repo="user/repo", token="t")
        assert host.get_name() == "github"

    def test_required_config(self):
        assert "repo" in GitHubImageHost.required_config()
        assert "token" in GitHubImageHost.required_config()


class TestCloudinaryImageHost:
    def test_name(self):
        host = CloudinaryImageHost(cloud_name="test")
        assert host.get_name() == "cloudinary"

    def test_required_config(self):
        assert "cloud_name" in CloudinaryImageHost.required_config()

    def test_optional_config(self):
        opts = CloudinaryImageHost.optional_config()
        assert "upload_preset" in opts
        assert "api_key" in opts


class TestBuildHostConfig:
    def test_unknown_host(self):
        with pytest.raises(ValueError, match="Unknown host"):
            build_host_config("nonexistent", {})

    def test_missing_required(self):
        with pytest.raises(ValueError, match="Missing required config"):
            build_host_config("github", {})

    def test_github_with_args(self):
        config = build_host_config("github", {"repo": "r", "token": "t"})
        assert config["repo"] == "r"
        assert config["token"] == "t"
        assert config["path_prefix"] == "images"

    def test_oss_with_args(self):
        config = build_host_config("oss", {
            "endpoint": "oss-cn-hangzhou.aliyuncs.com",
            "bucket": "b", "access_key": "ak", "secret_key": "sk",
        })
        assert config["endpoint"] == "oss-cn-hangzhou.aliyuncs.com"
        assert config["path_prefix"] == "images"

    def test_cloudinary_with_args(self):
        config = build_host_config("cloudinary", {"cloud_name": "c"})
        assert config["cloud_name"] == "c"
        assert config["upload_preset"] == "unsigned"


def test_host_registry_has_known_hosts():
    assert "oss" in HOST_REGISTRY
    assert "github" in HOST_REGISTRY
    assert "cloudinary" in HOST_REGISTRY