import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

BUILTIN_DIR = Path(__file__).parent / "builtin"

TEMPLATE_EXTENSIONS = ["*.j2", "*.html"]


class TemplateManager:
    def __init__(self, custom_dirs: list[Path] | None = None):
        search_paths = [BUILTIN_DIR]
        if custom_dirs:
            search_paths.extend(custom_dirs)

        self.env = Environment(
            loader=FileSystemLoader([str(p) for p in search_paths]),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        self.env.filters["wrap"] = self._wrap_filter
        self.env.filters["truncate"] = self._truncate_filter

    @staticmethod
    def _wrap_filter(value: str, quote: str = '"') -> str:
        return f"{quote}{value}{quote}"

    @staticmethod
    def _truncate_filter(value: str, length: int = 100, suffix: str = "...") -> str:
        if len(value) <= length:
            return value
        return value[:length].rstrip() + suffix

    def list_templates(self) -> list[dict]:
        templates = []
        seen = set()
        for search_path in self.env.loader.searchpath:
            p = Path(search_path)
            if not p.exists():
                continue
            for ext in TEMPLATE_EXTENSIONS:
                for f in sorted(p.glob(ext)):
                    if f.name in seen:
                        continue
                    seen.add(f.name)
                    name = f.name
                    for suffix in (".j2", ".html"):
                        if name.endswith(suffix):
                            name = name[:-len(suffix)]
                            break
                    if "." in name:
                        name = name.rsplit(".", 1)[0]
                    templates.append({
                        "name": name,
                        "file": f.name,
                        "path": str(f),
                        "builtin": p == BUILTIN_DIR,
                    })
        return templates

    def render(self, template_name: str, body: str,
               metadata: dict, front_matter: str = "",
               footnotes: str = "") -> str:
        tpl = self.env.get_template(template_name)
        return tpl.render(
            body=body,
            metadata=metadata,
            front_matter=front_matter,
            footnotes=footnotes,
        )

    def render_from_body(self, template_name: str, body: str,
                         metadata: dict) -> str:
        return self.render(template_name, body, metadata)


def create_manager(custom_dirs: list[Path] | None = None) -> TemplateManager:
    return TemplateManager(custom_dirs=custom_dirs)