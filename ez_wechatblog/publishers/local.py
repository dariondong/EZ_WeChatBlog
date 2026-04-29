import logging
from pathlib import Path

from ez_wechatblog.publishers.base import Article, BasePublisher
from ez_wechatblog.utils import ensure_dir, sanitize_filename

logger = logging.getLogger(__name__)


class LocalPublisher(BasePublisher):
    def get_name(self) -> str:
        return "local"

    def get_slug(self, article: Article) -> str:
        title = article.metadata.get("title", "untitled")
        return sanitize_filename(title)

    def publish(self, article: Article, config: dict) -> dict:
        output_dir_str = config.get("output_dir", "./output")
        output_dir = ensure_dir(Path(output_dir_str))
        slug = config.get("slug") or self.get_slug(article)
        article_dir = ensure_dir(output_dir / slug)

        md_path = article_dir / "index.md"
        md_path.write_text(article.markdown, encoding="utf-8")

        if article.assets_dir and article.assets_dir.exists():
            dest_assets = ensure_dir(article_dir / "images")
            for f in article.assets_dir.iterdir():
                if f.is_file():
                    dest_path = dest_assets / f.name
                    if not dest_path.exists():
                        import shutil
                        shutil.copy2(f, dest_path)

        logger.info("Published to %s", article_dir)
        return {
            "publisher": "local",
            "slug": slug,
            "path": str(article_dir),
            "md_path": str(md_path),
        }