import logging
import shutil
from pathlib import Path

from ez_wechatblog.publishers.base import Article, BasePublisher
from ez_wechatblog.utils import ensure_dir, sanitize_filename

logger = logging.getLogger(__name__)


class HexoPublisher(BasePublisher):
    def get_name(self) -> str:
        return "hexo"

    def get_slug(self, article: Article) -> str:
        title = article.metadata.get("title", "untitled")
        return sanitize_filename(title)

    def publish(self, article: Article, config: dict) -> dict:
        output_dir_str = config.get("output_dir", "./output")
        output_dir = ensure_dir(Path(output_dir_str))
        slug = config.get("slug") or self.get_slug(article)
        source_dir = ensure_dir(output_dir / "source" / "_posts")

        try:
            md_path = source_dir / f"{slug}.md"
            md_path.write_text(article.markdown, encoding="utf-8")
        except OSError as e:
            raise RuntimeError(f"Failed to write {md_path}: {e}") from e

        if article.assets_dir and article.assets_dir.exists():
            dest_assets = ensure_dir(source_dir / "images")
            for f in article.assets_dir.iterdir():
                if f.is_file():
                    dest_path = dest_assets / f.name
                    if not dest_path.exists():
                        try:
                            shutil.copy2(f, dest_path)
                        except OSError as e:
                            logger.warning("Failed to copy %s: %s", f, e)

        logger.info("Published to Hexo: %s", md_path)
        return {
            "publisher": "hexo",
            "slug": slug,
            "path": str(md_path),
            "md_path": str(md_path),
        }