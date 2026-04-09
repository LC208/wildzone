"""
parsing/scrapers/base.py

Базовые типы и абстрактный класс для всех скраперов.

Изменения:
- search() / _search() принимают page, sorting, dest
- async_search() — throttling через Semaphore
- Retry-декоратор сохранён
"""

from __future__ import annotations

from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed
import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import wraps
from typing import Callable, Optional, Type
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

MAX_CONCURRENT_REQUESTS: int = getattr(settings, "PARSING_MAX_CONCURRENT", 3)


def retry(
    attempts: int = 3,
    delay: float = 1.0,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
    backoff: float = 1.0,
):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            _attempt = 0
            _max_attempts = getattr(settings, "PARSING_RETRY_ATTEMPTS", attempts)
            _delay = getattr(settings, "PARSING_RETRY_DELAY", delay)

            while _attempt < _max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    _attempt += 1
                    if _attempt >= _max_attempts:
                        logger.exception(
                            "❌ %s failed after %s attempts",
                            func.__qualname__,
                            _attempt,
                        )
                        raise
                    logger.warning(
                        "⚠️ %s failed (attempt %s/%s): %s. Retrying in %.2fs",
                        func.__qualname__,
                        _attempt,
                        _max_attempts,
                        repr(e),
                        _delay,
                    )
                    time.sleep(_delay)
                    _delay *= backoff

        return wrapper

    return decorator


@dataclass
class ProductData:
    external_id: str
    title: str
    url: str
    marketplace: str = ""
    article: str = ""
    price: Optional[float] = None
    original_price: Optional[float] = None
    brand: str = ""
    rating: Optional[float] = None
    reviews_count: int = 0
    in_stock: bool = True
    delivery_days: Optional[int] = None
    image_url: str = ""
    category: str = ""
    attributes: dict = field(default_factory=dict)


class BaseScraper(ABC):
    marketplace: str = ""
    ipp: int = 4 
    _semaphore: Optional[asyncio.Semaphore] = None

    def __init__(self) -> None:
        self._delay: float = settings.PARSING_REQUEST_DELAY

    @retry(
        attempts=getattr(settings, "PARSING_RETRY_ATTEMPTS", 3),
        delay=getattr(settings, "PARSING_RETRY_DELAY", 1.0),
        backoff=2,
    )
    def search(
        self,
        query: str,
        page: int = 1,
        sorting: Optional[str] = None,
        dest: Optional[int] = None,
    ) -> list[ProductData]:
        """
        Синхронный поиск.

        :param query:   Поисковый запрос.
        :param page:    Номер страницы (начиная с 1).
        :param sorting: Унифицированный ключ сортировки.
        :param dest:    WB dest-код региона (для WB-скрапера).
                        None → скрапер использует свой дефолт.
        """
        return self._search(query, page=page, sorting=sorting, dest=dest)

    async def async_search(
        self,
        query: str,
        page: int = 1,
        sorting: Optional[str] = None,
        dest: Optional[int] = None,
    ) -> list[ProductData]:
        """
        Асинхронная обёртка с throttling.
        """
        if self.__class__._semaphore is None:
            self.__class__._semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

        async with self.__class__._semaphore:
            loop = asyncio.get_event_loop()

            async for attempt in AsyncRetrying(stop=stop_after_attempt(3), wait=wait_fixed(5)):
                with attempt:
                    result = await loop.run_in_executor(
                        None,
                        lambda: self._search(query, page=page, sorting=sorting, dest=dest)
                    )
                    return result

    @abstractmethod
    def _search(
        self,
        query: str,
        page: int = 1,
        sorting: Optional[str] = None,
        dest: Optional[int] = None,
    ) -> list[ProductData]:
        ...

    def _sleep(self) -> None:
        time.sleep(self._delay)
