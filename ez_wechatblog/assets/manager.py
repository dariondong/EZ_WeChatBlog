import asyncio
import base64
import hashlib
import hmac
import logging
import os
import re
import time
from abc import ABC, abstractmethod
from pathlib import Path
from urllib.parse import urlparse, quote

import aiohttp

from ez_wechatblog.utils import ensure_dir, get_ext_from_url, get_safe_filename

logger = logging.getLogger(__name__)


class ImageHost(ABC):
    @abstractmethod
    def get_name(self) -> str:
        ...

    @abstractmethod
    async def upload(self, image_data: bytes, filename: str,
                     session: aiohttp.ClientSession) -> str:
        ...

    @classmethod
    def required_config(cls) -> list[str]:
        return []

    @classmethod
    def optional_config(cls) -> dict[str, str]:
        return {}


class OSSImageHost(ImageHost):
    def __init__(self, endpoint: str = "", bucket: str = "",
                 access_key: str = "", secret_key: str = "",
                 path_prefix: str = "images"):
        self.endpoint = endpoint.replace("https://", "").replace("http://", "").rstrip("/")
        self.bucket = bucket
        self.access_key = access_key
        self.secret_key = secret_key
        self.path_prefix = path_prefix

    def get_name(self) -> str:
        return "oss"

    @classmethod
    def required_config(cls) -> list[str]:
        return ["endpoint", "bucket", "access_key", "secret_key"]

    @classmethod
    def optional_config(cls) -> dict[str, str]:
        return {"path_prefix": "images"}

    async def upload(self, image_data: bytes, filename: str,
                     session: aiohttp.ClientSession) -> str:
        resource = f"/{self.bucket}/{self.path_prefix}/{filename}"
        content_type = self._guess_content_type(filename)
        date = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())

        string_to_sign = f"PUT\n\n{content_type}\n{date}\n{resource}"
        signature = base64.b64encode(
            hmac.new(self.secret_key.encode(), string_to_sign.encode(),
                     hashlib.sha1).digest()
        ).decode()

        url = f"https://{self.bucket}.{self.endpoint}/{self.path_prefix}/{filename}"
        headers = {
            "Date": date,
            "Content-Type": content_type,
            "Authorization": f"OSS {self.access_key}:{signature}",
        }

        async with session.put(url, data=image_data, headers=headers,
                               timeout=aiohttp.ClientTimeout(total=60)) as resp:
            if resp.status == 200:
                logger.info("OSS uploaded: %s", url)
                return url
            body = await resp.text()
            raise RuntimeError(f"OSS upload failed: {resp.status} {body[:200]}")

    @staticmethod
    def _guess_content_type(filename: str) -> str:
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "png"
        return {
            "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "gif": "image/gif", "webp": "image/webp", "svg": "image/svg+xml",
            "bmp": "image/bmp",
        }.get(ext, "application/octet-stream")


class GitHubImageHost(ImageHost):
    def __init__(self, repo: str = "", token: str = "",
                 path_prefix: str = "images"):
        self.repo = repo
        self.token = token
        self.path_prefix = path_prefix

    def get_name(self) -> str:
        return "github"

    @classmethod
    def required_config(cls) -> list[str]:
        return ["repo", "token"]

    @classmethod
    def optional_config(cls) -> dict[str, str]:
        return {"path_prefix": "images"}

    async def upload(self, image_data: bytes, filename: str,
                     session: aiohttp.ClientSession) -> str:
        gh_path = f"{self.path_prefix}/{filename}"
        url = f"https://api.github.com/repos/{self.repo}/contents/{gh_path}"
        encoded = base64.b64encode(image_data).decode()
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }

        sha = None
        async with session.get(url, headers=headers,
                               timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status == 200:
                data = await resp.json()
                sha = data.get("sha")

        payload = {"message": f"Upload {filename}", "content": encoded}
        if sha:
            payload["sha"] = sha

        async with session.put(url, json=payload, headers=headers,
                               timeout=aiohttp.ClientTimeout(total=30)) as resp:
            if resp.status in (200, 201):
                data = await resp.json()
                return data["content"]["download_url"]
            body = await resp.text()
            raise RuntimeError(f"GitHub upload failed: {resp.status} {body[:200]}")


class CloudinaryImageHost(ImageHost):
    def __init__(self, cloud_name: str = "", api_key: str = "",
                 api_secret: str = "", upload_preset: str = ""):
        self.cloud_name = cloud_name
        self.api_key = api_key
        self.api_secret = api_secret
        self.upload_preset = upload_preset

    def get_name(self) -> str:
        return "cloudinary"

    @classmethod
    def required_config(cls) -> list[str]:
        return ["cloud_name"]

    @classmethod
    def optional_config(cls) -> dict[str, str]:
        return {"api_key": "", "api_secret": "", "upload_preset": "unsigned"}

    async def upload(self, image_data: bytes, filename: str,
                     session: aiohttp.ClientSession) -> str:
        url = f"https://api.cloudinary.com/v1_1/{self.cloud_name}/image/upload"
        data = aiohttp.FormData()
        data.add_field("file", image_data, filename=filename,
                       content_type="application/octet-stream")

        if self.api_key and self.api_secret:
            timestamp = str(int(time.time()))
            params_to_sign = f"timestamp={timestamp}{self.api_secret}"
            signature = hashlib.sha1(params_to_sign.encode()).hexdigest()
            data.add_field("api_key", self.api_key)
            data.add_field("timestamp", timestamp)
            data.add_field("signature", signature)
        elif self.upload_preset:
            data.add_field("upload_preset", self.upload_preset)
        else:
            data.add_field("upload_preset", "unsigned")

        async with session.post(url, data=data,
                                timeout=aiohttp.ClientTimeout(total=60)) as resp:
            if resp.status == 200:
                result = await resp.json()
                return result["secure_url"]
            body = await resp.text()
            raise RuntimeError(f"Cloudinary upload failed: {resp.status} {body[:200]}")


HOST_REGISTRY: dict[str, type[ImageHost]] = {
    "oss": OSSImageHost,
    "github": GitHubImageHost,
    "cloudinary": CloudinaryImageHost,
}


def build_host_config(host_type: str, cli_args: dict | None = None,
                      env_prefix: str = "EZ_WC_IMG") -> dict:
    if host_type not in HOST_REGISTRY:
        available = list(HOST_REGISTRY.keys())
        raise ValueError(f"Unknown host '{host_type}'. Available: {available}")

    host_cls = HOST_REGISTRY[host_type]
    config: dict = {}

    for key in host_cls.required_config():
        val = (cli_args or {}).get(key)
        if not val:
            env_key = f"{env_prefix}_{host_type.upper()}_{key.upper()}"
            val = os.environ.get(env_key)
        if not val:
            raise ValueError(
                f"Missing required config '{key}' for {host_type}. "
                f"Pass via --image-config or set {env_prefix}_{host_type.upper()}_{key.upper()}"
            )
        config[key] = val

    for key, default in host_cls.optional_config().items():
        val = (cli_args or {}).get(key) or default
        if not val:
            env_key = f"{env_prefix}_{host_type.upper()}_{key.upper()}"
            val = os.environ.get(env_key, default)
        config[key] = val

    return config


def _guess_mime(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "png"
    return {
        "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "gif": "image/gif", "webp": "image/webp", "svg": "image/svg+xml",
        "bmp": "image/bmp",
    }.get(ext, "image/png")


class AssetManager:
    def __init__(self, output_dir: Path, assets_subdir: str = "images",
                 max_concurrent: int = 5, referer: str = "",
                 image_mode: str = "local", image_host: ImageHost | None = None):
        self.output_dir = output_dir
        self.assets_subdir = assets_subdir
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.referer = referer
        self.image_mode = image_mode
        self.image_host = image_host
        self._mapping: dict[str, str] = {}

        if image_mode == "local":
            self.assets_dir = ensure_dir(output_dir / assets_subdir)
        else:
            self.assets_dir = output_dir / assets_subdir

    @property
    def mapping(self) -> dict[str, str]:
        return dict(self._mapping)

    async def download_all(self, urls: list[str]) -> list[tuple[str, str]]:
        connector = aiohttp.TCPConnector(limit=10)
        headers = {"User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        )}
        if self.referer:
            headers["Referer"] = self.referer

        async with aiohttp.ClientSession(connector=connector,
                                         headers=headers) as session:
            tasks = [self._process_one(session, url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        downloaded = []
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                logger.warning("Failed to process %s: %s", url, result)
                continue
            if result:
                downloaded.append(result)
                self._mapping[url] = result[1]
        return downloaded

    async def _process_one(self, session: aiohttp.ClientSession,
                           url: str) -> tuple[str, str] | None:
        async with self.semaphore:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(
                        total=30)) as resp:
                    if resp.status != 200:
                        logger.warning("HTTP %d for %s", resp.status, url)
                        return None
                    data = await resp.read()
            except Exception as e:
                logger.error("Download error for %s: %s", url[:60], e)
                return None

            ext = get_ext_from_url(url)
            filename = get_safe_filename(url, ext)

            return await self._store_image(data, filename, url, session)

    async def _store_image(self, data: bytes, filename: str,
                           original_url: str,
                           session: aiohttp.ClientSession | None = None) -> tuple[str, str]:
        if self.image_mode == "local":
            return await self._store_local(data, filename)
        elif self.image_mode == "base64":
            return await self._store_base64(data, filename)
        elif self.image_mode == "remote":
            return await self._store_remote(data, filename, session)
        return await self._store_local(data, filename)

    async def _store_local(self, data: bytes, filename: str) -> tuple[str, str]:
        ensure_dir(self.output_dir / self.assets_subdir)
        dest = self.assets_dir / filename
        dest.write_bytes(data)
        relative = f"{self.assets_subdir}/{dest.name}"
        logger.info("Saved locally: %s", relative)
        return "", relative

    async def _store_base64(self, data: bytes, filename: str) -> tuple[str, str]:
        encoded = base64.b64encode(data).decode()
        mime = _guess_mime(filename)
        data_uri = f"data:{mime};base64,{encoded}"
        logger.info("Encoded base64: %s (%d bytes)", filename, len(encoded))
        return "", data_uri

    async def _store_remote(self, data: bytes, filename: str,
                            session: aiohttp.ClientSession | None = None) -> tuple[str, str]:
        if self.image_host is None:
            raise RuntimeError("No image host configured for remote mode")
        own_session = session is None
        if own_session:
            session = aiohttp.ClientSession()
        try:
            url = await self.image_host.upload(data, filename, session=session)
            logger.info("Uploaded: %s -> %s", filename, url)
            return "", url
        finally:
            if own_session:
                await session.close()

    def rewrite_markdown_images(self, markdown: str) -> str:
        pattern = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")

        def replacer(m: re.Match) -> str:
            alt = m.group(1)
            original_url = m.group(2)
            local = self._mapping.get(original_url)
            if local:
                return f"![{alt}]({local})"
            return m.group(0)

        return pattern.sub(replacer, markdown)