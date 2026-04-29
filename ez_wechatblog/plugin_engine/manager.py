import logging
from pathlib import Path

import pluggy

from ez_wechatblog.publishers.base import Article, BasePublisher
from ez_wechatblog.publishers.local import LocalPublisher

logger = logging.getLogger(__name__)

HOOK_SPEC = "ez_wechatblog_publisher"
_hook_impl = pluggy.HookimplMarker(HOOK_SPEC)
_hook_spec = pluggy.HookspecMarker(HOOK_SPEC)


class PublisherProject:
    @_hook_spec
    def publish(self, article: Article, config: dict) -> dict:
        ...


class PluginManager:
    def __init__(self):
        self._pm = pluggy.PluginManager(HOOK_SPEC)
        self._pm.add_hookspecs(PublisherProject)
        self._builtin_publishers: dict[str, BasePublisher] = {}

    def register_builtin(self, publisher: BasePublisher):
        name = publisher.get_name()
        self._builtin_publishers[name] = publisher
        logger.info("Registered built-in publisher: %s", name)

    def get_publisher(self, name: str) -> BasePublisher | None:
        return self._builtin_publishers.get(name)

    def list_publishers(self) -> list[str]:
        return list(self._builtin_publishers.keys())

    def discover_plugins(self, plugin_dirs: list[Path] | None = None):
        if not plugin_dirs:
            return

    def publish(self, article: Article, publisher_name: str,
                config: dict | None = None) -> dict:
        config = config or {}
        publisher = self.get_publisher(publisher_name)
        if publisher is None:
            raise ValueError(f"Unknown publisher '{publisher_name}'."
                             f" Available: {self.list_publishers()}")
        return publisher.publish(article, config)


def create_manager() -> PluginManager:
    pm = PluginManager()
    pm.register_builtin(LocalPublisher())
    return pm