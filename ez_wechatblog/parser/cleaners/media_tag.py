import re
from bs4 import BeautifulSoup, Tag


def clean_media_tags(soup: BeautifulSoup) -> None:
    _clean_videos(soup)
    _clean_audio(soup)
    _clean_images(soup)
    _clean_links(soup)


def _clean_videos(soup: BeautifulSoup) -> None:
    for tag in soup.find_all("mpvideo"):
        vid = tag.get("data-vid", "")
        replace_with = soup.new_tag("p")
        link = soup.new_tag("a",
                            href=f"https://mp.weixin.qq.com/mp/read?vid={vid}",
                            target="_blank")
        link.string = f"[视频: {vid}]" if vid else "[视频]"
        replace_with.append(link)
        tag.replace_with(replace_with)

    for tag in soup.find_all(["video", "iframe"]):
        if isinstance(tag, Tag) and tag.name == "iframe":
            src = tag.get("src", "")
            if "video" in src.lower() or "mp.weixin.qq.com" in src:
                tag.decompose()
        elif isinstance(tag, Tag):
            tag.decompose()


def _clean_audio(soup: BeautifulSoup) -> None:
    for tag in soup.find_all("mpvoice"):
        name = tag.get("data-name", "") or "音频"
        replace_with = soup.new_tag("p")
        link = soup.new_tag("a",
                            href="https://mp.weixin.qq.com/",
                            target="_blank")
        link.string = f"[音频: {name}]"
        replace_with.append(link)
        tag.replace_with(replace_with)

    for tag in soup.find_all("audio"):
        tag.decompose()


def _clean_images(soup: BeautifulSoup) -> None:
    for img in soup.find_all("img"):
        if not isinstance(img, Tag):
            continue
        data_src = img.get("data-src")
        src = img.get("src", "")
        if data_src:
            img["src"] = data_src
            del img["data-src"]
        if not img.get("src") and not data_src:
            img.decompose()


def _clean_links(soup: BeautifulSoup) -> None:
    for a_tag in soup.find_all("a"):
        if not isinstance(a_tag, Tag):
            continue
        href = a_tag.get("href", "")
        if not href or href.startswith("javascript"):
            a_tag.unwrap()