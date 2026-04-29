import re
import uuid
from pathlib import Path
from urllib.parse import urlparse, unquote


def sanitize_filename(name: str, max_length: int = 80) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|!]', "_", name)
    cleaned = re.sub(r"\s+", "_", cleaned).strip("._")
    if not cleaned:
        cleaned = "untitled"
    return cleaned[:max_length]


def extract_slug(url: str) -> str | None:
    match = re.search(r"mp\.weixin\.qq\.com/s/([A-Za-z0-9_-]+)", url)
    if match:
        return match.group(1)
    return None


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)


def validate_url(url: str) -> str:
    if not url or not url.strip():
        raise ValueError("URL 不能为空")
    url = url.strip()
    parsed = urlparse(url)
    if not parsed.scheme:
        raise ValueError(f"URL 缺少协议: {url}（需要 http:// 或 https://）")
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"不支持的协议: {parsed.scheme}（需要 http 或 https）")
    if not parsed.netloc:
        raise ValueError(f"URL 格式无效: {url}")
    return url


def get_ext_from_url(url: str) -> str:
    path = unquote(urlparse(url).path)
    match = re.search(r"\.(png|jpg|jpeg|gif|webp|bmp|svg)", path, re.IGNORECASE)
    return match.group(1).lower() if match else "jpg"


def get_safe_filename(original: str, ext: str = "") -> str:
    parsed = urlparse(original)
    filename = parsed.path.split("/")[-1] or "image"
    if "." not in filename:
        filename = f"{filename}.{ext}" if ext else f"{filename}.jpg"
    stem = Path(filename).stem
    suffix = Path(filename).suffix or f".{ext}" if ext else ".jpg"
    unique = uuid.uuid4().hex[:8]
    return f"{stem}_{unique}{suffix}"