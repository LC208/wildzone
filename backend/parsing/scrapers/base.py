"""
parsing/scrapers/base.py

Базовые типы и абстрактный класс для всех скраперов.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from functools import wraps
from typing import Callable, Type
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


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

    def __init__(self) -> None:
        self._delay: float = settings.PARSING_REQUEST_DELAY

    @retry(
        attempts=getattr(settings, "PARSING_RETRY_ATTEMPTS", 3),
        delay=getattr(settings, "PARSING_RETRY_DELAY", 1.0),
        backoff=2,
    )
    def search(self, query: str, max_results: int = 20) -> list[ProductData]:
        return self._search(query, max_results)

    @abstractmethod
    def _search(self, query: str, max_results: int) -> list[ProductData]:
        ...

    def _sleep(self) -> None:
        time.sleep(self._delay)