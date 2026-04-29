from ez_wechatblog.fetcher.base import BaseFetcher


class FetcherFactory:
    _fetchers: dict[str, type[BaseFetcher]] = {}

    @classmethod
    def register(cls, name: str):
        def decorator(fetcher_cls: type[BaseFetcher]):
            cls._fetchers[name] = fetcher_cls
            return fetcher_cls

        return decorator

    @classmethod
    def create(cls, name: str = "playwright", **kwargs) -> BaseFetcher:
        if name not in cls._fetchers:
            available = list(cls._fetchers.keys())
            msg = f"Unknown fetcher '{name}'. Available: {available}"
            raise ValueError(msg)
        return cls._fetchers[name](**kwargs)