from abc import ABC, abstractmethod


class BaseFetcher(ABC):
    @abstractmethod
    async def fetch(self, url: str) -> str:
        ...

    @abstractmethod
    async def close(self):
        ...