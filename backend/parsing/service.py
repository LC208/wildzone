"""
parsing/service.py

Оркестратор парсинга.

Запускает нужные парсеры и возвращает список ProductData напрямую.
Никакой записи в БД — данные живут только в памяти в рамках запроса.
В БД попадает только то, что пользователь явно сохранит в избранное.
"""

import logging
from typing import List

from .scrapers.base import ProductData
from .scrapers.wildberries import WildberriesScraper
from .scrapers.ozon import OzonScraper

logger = logging.getLogger(__name__)

SCRAPERS = {
    "wb":   WildberriesScraper,
    "ozon": OzonScraper,
}


def run_search(
    query: str,
    marketplaces: List[str] = None,
    max_per_mp: int = 20,
) -> List[ProductData]:
    """
    Запустить поиск по маркетплейсам и вернуть список ProductData.
    Результаты НЕ сохраняются в БД.
    """
    if marketplaces is None:
        marketplaces = list(SCRAPERS.keys())

    results: List[ProductData] = []
    for mp_key in marketplaces:
        scraper_cls = SCRAPERS.get(mp_key)
        if not scraper_cls:
            logger.warning("Неизвестный маркетплейс: %s", mp_key)
            continue
        try:
            items = scraper_cls().search(query, max_results=max_per_mp)
            results.extend(items)
        except Exception as exc:
            logger.error("Ошибка парсинга %s: %s", mp_key, exc)

    return results