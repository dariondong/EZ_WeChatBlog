import asyncio
import logging
from pathlib import Path
from urllib.parse import urlparse

import aiohttp

from ez_wechatblog.utils import ensure_dir, get_ext_from_url

logger = logging.getLogger(__name__)


class AssetManager:
    def __init__(self, output_dir: Path, assets_subdir: str = "images",
                 max_concurrent: int = 5, referer: str = ""):
        self.output_dir = output_dir
        self.assets_dir = ensure_dir(output_dir / assets_subdir)
        self.assets_subdir = assets_subdir
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.referer = referer
        self._mapping: dict[str, str] = {}

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
            tasks = [self._download_one(session, url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        downloaded = []
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                logger.warning("Failed to download %s: %s", url, result)
                continue
            if result:
                downloaded.append(result)
                self._mapping[url] = result[1]
        return downloaded

    async def _download_one(self, session: aiohttp.ClientSession,
                            url: str) -> tuple[str, str] | None:
        async with self.semaphore:
            ext = get_ext_from_url(url)
            parsed = urlparse(url)
            filename = parsed.path.split("/")[-1] or f"image"
            if "." not in filename:
                filename = f"{filename}.{ext}"
            dest = self.assets_dir / filename

            counter = 1
            while dest.exists():
                stem = dest.stem
                dest = self.assets_dir / f"{stem}_{counter}{dest.suffix}"
                counter += 1

            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(
                        total=30)) as resp:
                    if resp.status != 200:
                        logger.warning("HTTP %d for %s", resp.status, url)
                        return None
                    data = await resp.read()
                    dest.write_bytes(data)
                    relative = f"{self.assets_subdir}/{dest.name}"
                    logger.info("Downloaded: %s -> %s", url[:60], relative)
                    return url, relative
            except Exception as e:
                logger.error("Download error for %s: %s", url[:60], e)
                return None

    def rewrite_markdown_images(self, markdown: str) -> str:
        import re
        pattern = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")

        def replacer(m: re.Match) -> str:
            alt = m.group(1)
            original_url = m.group(2)
            local = self._mapping.get(original_url)
            if local:
                return f"![{alt}]({local})"
            for orig, local_path in self._mapping.items():
                if orig.endswith(original_url) or original_url in orig:
                    return f"![{alt}]({local_path})"
            return m.group(0)

        return pattern.sub(replacer, markdown)