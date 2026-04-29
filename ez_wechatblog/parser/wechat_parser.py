import re
from datetime import datetime

import yaml
from bs4 import BeautifulSoup, Tag
from markdownify import markdownify as md

from ez_wechatblog.parser.cleaners.code_snippet import clean_code_snippets
from ez_wechatblog.parser.cleaners.generic import full_clean
from ez_wechatblog.parser.cleaners.media_tag import clean_media_tags


class ArticleMeta:
    def __init__(self, title: str = "", author: str = "", date: str = "",
                 tags: list[str] | None = None, url: str = ""):
        self.title = title
        self.author = author
        self.date = date or datetime.now().strftime("%Y-%m-%d")
        self.tags = tags or []
        self.url = url

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "author": self.author,
            "date": self.date,
            "tags": self.tags,
            "url": self.url,
        }


class WeChatParser:
    IMAGE_PATTERN = re.compile(r"<img[^>]+src=['\"]([^'\"]+)['\"]")

    def parse(self, html: str, url: str = "") -> tuple[str, ArticleMeta, list[str], str]:
        if not html or not html.strip():
            raise ValueError("HTML 内容为空")

        soup = BeautifulSoup(html, "html.parser")

        content = self._extract_content(soup)
        if content is None:
            raise ValueError("无法找到文章正文 (#js_content)，请检查 URL 是否为微信公众号文章")

        clean_code_snippets(content, soup=soup)
        clean_media_tags(content, soup=soup)
        full_clean(content)

        meta = self._extract_meta(soup, url)
        image_urls = self._extract_images(content)

        raw_html = str(content)
        markdown_body = self._to_markdown(raw_html)

        return markdown_body, meta, image_urls, raw_html

    def _extract_content(self, soup: BeautifulSoup) -> Tag | None:
        content = soup.find("div", id="js_content")
        if content is None or not isinstance(content, Tag):
            rich = soup.find("div", id="js_rich_content_container")
            if rich is not None and isinstance(rich, Tag):
                content = rich
            else:
                return None
        return content

    def _extract_meta(self, soup: BeautifulSoup, url: str) -> ArticleMeta:
        title = ""
        author = ""
        date_str = ""

        og_title = soup.find("meta", property="og:title")
        if og_title:
            title = og_title.get("content", "")

        if not title:
            title_tag = soup.find("title")
            if title_tag:
                title = title_tag.get_text(strip=True)

        activity = soup.find("em", id="publish_time")
        if activity:
            date_str = activity.get_text(strip=True)
            date_str = self._normalize_date(date_str)

        profile = soup.find("strong", id="profile_name")
        if profile:
            author = profile.get_text(strip=True)

        if not author and "weixin" in url:
            og_desc = soup.find("meta", property="og:description")
            if og_desc:
                desc = og_desc.get("content", "")
                match = re.search(r"作者[：:]\s*(\S+)", desc)
                if match:
                    author = match.group(1)

        return ArticleMeta(title=title or "Untitled",
                           author=author,
                           date=date_str,
                           url=url,
                           tags=[])

    def _normalize_date(self, date_str: str) -> str:
        match = re.search(r"(\d{4}-\d{2}-\d{2})", date_str)
        if match:
            return match.group(1)
        return datetime.now().strftime("%Y-%m-%d")

    def _extract_images(self, content: Tag) -> list[str]:
        urls = []
        for img in content.find_all("img"):
            if not isinstance(img, Tag):
                continue
            src = img.get("src") or ""
            if src and not src.startswith("data:"):
                urls.append(src)
        return urls

    def _to_markdown(self, html: str) -> str:
        body = md(html, heading_style="ATX", bullets="-",
                  strip=["style", "script"],
                  convert_a=True, code_language="")
        body = self._cleanup_markdown(body)
        return body.strip()

    def _cleanup_markdown(self, text: str) -> str:
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{4,}", "\n\n\n", text)
        return text

    def build_full_markdown(self, body: str, meta: ArticleMeta) -> str:
        front_matter = yaml.dump(meta.to_dict(), allow_unicode=True,
                                 default_flow_style=False, sort_keys=False)
        return f"---\n{front_matter}---\n\n{body}\n"