"""
parsing/scrapers/base.py

Базовые типы и абстрактный класс для всех скраперов.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from django.conf import settings


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

    @abstractmethod
    def search(self, query: str, max_results: int = 20) -> list[ProductData]: ...

    def _sleep(self) -> None:
        time.sleep(self._delay)
