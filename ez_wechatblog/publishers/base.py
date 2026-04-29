from abc import ABC, abstractmethod
from pathlib import Path


class Article:
    def __init__(self, markdown: str, metadata: dict,
                 assets_dir: Path | None = None):
        self.markdown = markdown
        self.metadata = metadata
        self.assets_dir = assets_dir


class BasePublisher(ABC):
    @abstractmethod
    def get_name(self) -> str:
        ...

    @abstractmethod
    def publish(self, article: Article, config: dict) -> dict:
        ...

    @abstractmethod
    def get_slug(self, article: Article) -> str:
        ...