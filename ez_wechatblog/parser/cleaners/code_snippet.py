from bs4 import BeautifulSoup, Tag


def clean_code_snippets(content: Tag, soup: BeautifulSoup | None = None) -> None:
    if soup is None:
        soup = BeautifulSoup("", "html.parser")

    for tag in content.find_all("code-snippet"):
        lang = tag.get("data-lang", "")
        code_text = tag.get_text()
        pre = soup.new_tag("pre")
        code_tag = soup.new_tag("code")
        if lang:
            code_tag["class"] = f"language-{lang}"
        code_tag.string = code_text
        pre.append(code_tag)
        tag.replace_with(pre)

    for tag in content.find_all("pre"):
        if not isinstance(tag, Tag):
            continue
        code_tag = tag.find("code")
        if code_tag is None:
            continue
        code_text = code_tag.get_text()
        lines = code_text.split("\n")
        common = _leading_whitespace(lines)
        if common > 0:
            tag_code = tag.find("code")
            if isinstance(tag_code, Tag):
                tag_code.string = "\n".join(l[common:] for l in lines)


def _leading_whitespace(lines: list[str]) -> int:
    non_empty = [l for l in lines if l.strip()]
    if not non_empty:
        return 0
    return min(len(l) - len(l.lstrip()) for l in non_empty)