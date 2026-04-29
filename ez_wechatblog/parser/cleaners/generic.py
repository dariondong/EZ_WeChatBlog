from bs4 import BeautifulSoup, Tag


def clean_inline_styles(content: Tag) -> None:
    for tag in content.find_all(True):
        if not isinstance(tag, Tag):
            continue
        if tag.name in ("style", "script", "link"):
            tag.decompose()
            continue
        if "style" in tag.attrs:
            del tag["style"]


def clean_empty_tags(content: Tag) -> None:
    for tag in content.find_all(["p", "div", "span", "section"]):
        if not isinstance(tag, Tag):
            continue
        text = tag.get_text(strip=True)
        if not text and not tag.find_all(["img", "video", "pre", "code", "a"]):
            tag.decompose()


def clean_section_tags(content: Tag) -> None:
    for tag in content.find_all("section"):
        if not isinstance(tag, Tag):
            continue
        tag.unwrap()


def clean_data_attrs(content: Tag) -> None:
    for tag in content.find_all(True):
        if not isinstance(tag, Tag):
            continue
        keys_to_del = [k for k in tag.attrs if k.startswith("data-")]
        for k in keys_to_del:
            del tag.attrs[k]

    for tag in content.find_all("img"):
        if not isinstance(tag, Tag):
            continue
        tag.attrs = {k: v for k, v in tag.attrs.items()
                     if k in ("src", "alt", "title", "width", "height")}


def clean_whitespace(content: Tag) -> None:
    for tag in content.find_all(True):
        if not isinstance(tag, Tag):
            continue
        if tag.string and tag.name not in ("pre", "code"):
            tag.string = tag.string.strip()


def full_clean(content: Tag) -> None:
    clean_inline_styles(content)
    clean_data_attrs(content)
    clean_section_tags(content)
    clean_empty_tags(content)
    clean_whitespace(content)