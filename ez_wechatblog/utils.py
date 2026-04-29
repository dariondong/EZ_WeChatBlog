import re
from pathlib import Path
from urllib.parse import urlparse, unquote


def sanitize_filename(name: str, max_length: int = 80) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|!]', "_", name)
    cleaned = re.sub(r"\s+", "_", cleaned).strip("._")
    if not cleaned:
        cleaned = "untitled"
    return cleaned[:max_length]


def extract_slug(url: str) -> str | None:
    match = re.search(r"/(s|mp.weixin.qq.com/s)/([A-Za-z0-9_-]+)", url)
    if match:
        return match.group(2)
    return None


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)


def get_ext_from_url(url: str) -> str:
    path = unquote(urlparse(url).path)
    match = re.search(r"\.(png|jpg|jpeg|gif|webp|bmp|svg)", path, re.IGNORECASE)
    return match.group(1).lower() if match else "jpg"