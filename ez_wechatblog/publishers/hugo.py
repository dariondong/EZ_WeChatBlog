import logging
from pathlib import Path

from ez_wechatblog.publishers.base import Article, BasePublisher
from ez_wechatblog.utils import ensure_dir, sanitize_filename

logger = logging.getLogger(__name__)


class HugoPublisher(BasePublisher):
    def get_name(self) -> str:
        return "hugo"

    def get_slug(self, article: Article) -> str:
        title = article.metadata.get("title", "untitled")
        return sanitize_filename(title).lower()

    def publish(self, article: Article, config: dict) -> dict:
        output_dir_str = config.get("output_dir", "./output")
        output_dir = ensure_dir(Path(output_dir_str))
        slug = config.get("slug") or self.get_slug(article)
        content_dir = ensure_dir(output_dir / "content" / "posts" / slug)

        md_path = content_dir / "index.md"
        md_path.write_text(article.markdown, encoding="utf-8")

        if article.assets_dir and article.assets_dir.exists():
            dest_assets = ensure_dir(content_dir / "images")
            for f in article.assets_dir.iterdir():
                if f.is_file():
                    dest_path = dest_assets / f.name
                    if not dest_path.exists():
                        import shutil
                        shutil.copy2(f, dest_path)

        logger.info("Published to Hugo: %s", content_dir)
        return {
            "publisher": "hugo",
            "slug": slug,
            "path": str(content_dir),
            "md_path": str(md_path),
        }