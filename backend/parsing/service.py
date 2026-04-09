"""
parsing/service.py

Оркестратор парсинга.

Изменения:
- run_search принимает dest (int, опционально)
- Если dest не передан — resolve_dest() вызывается только при наличии
  координат; иначе используется DEFAULT_DEST
- WB-скрапер получает dest, Ozon-скрапер — игнорирует
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging
from typing import List, Optional

from .geo import DEFAULT_DEST, resolve_dest
from .scrapers.base import ProductData
from .scrapers.wildberries import WildberriesScraper
from .scrapers.ozon import OzonScraper

logger = logging.getLogger(__name__)

SCRAPERS = {
    "wb":   WildberriesScraper,
    "ozon": OzonScraper,
}

ITEM_PER_SCRAPPER = 4

async def _run_search_async(
    query: str,
    marketplaces: List[str],
    page: int,
    sorting: Optional[str],
    dest: int,
) -> List[ProductData]:
    """Параллельный поиск по нескольким маркетплейсам."""

    async def _fetch(mp_key: str) -> List[ProductData]:
        scraper_cls = SCRAPERS.get(mp_key)
        if not scraper_cls:
            logger.warning("Неизвестный маркетплейс: %s", mp_key)
            return []
        try:
            return await scraper_cls().async_search(
                query, page=page, sorting=sorting, dest=dest
            )
        except Exception as exc:
            logger.error("Ошибка парсинга %s: %s", mp_key, exc)
            return []

    results_per_mp = await asyncio.gather(*[_fetch(mp) for mp in marketplaces])
    combined: List[ProductData] = []
    for items in results_per_mp:
        combined.extend(items)
    return combined


def run_search(
    query: str,
    marketplaces: List[str] = None,
    page: int = 1,
    sorting: Optional[str] = None,
    dest: Optional[int] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    address: str = "",
) -> List[ProductData]:
    """
    Синхронная точка входа.

    Геолокация (влияет только на WB):
      - Если передан dest напрямую — используется он.
      - Если переданы latitude + longitude — вызывается resolve_dest().
      - Иначе — DEFAULT_DEST (Иркутск).

    :param query:        Поисковый запрос.
    :param marketplaces: ['wb', 'ozon'] или None (все).
    :param page:         Номер страницы (начиная с 1).
    :param sorting:      Унифицированный ключ сортировки.
    :param dest:         WB dest-код (приоритет над координатами).
    :param latitude:     Широта для автоопределения dest.
    :param longitude:    Долгота для автоопределения dest.
    :param address:      Человекочитаемый адрес (необязательно).
    """
    if marketplaces is None:
        marketplaces = list(SCRAPERS.keys())

    # Определяем dest
    if dest is not None:
        effective_dest = dest
    elif latitude is not None and longitude is not None:
        effective_dest = resolve_dest(latitude, longitude, address)
    else:
        effective_dest = DEFAULT_DEST

    logger.debug("[Service] dest=%d, marketplaces=%s", effective_dest, marketplaces)

    coro = _run_search_async(query, marketplaces, page, sorting, effective_dest)

    try:
        loop = asyncio.get_running_loop()
        # Если уже есть running loop, запускаем через run_coroutine_threadsafe
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result()
    except RuntimeError:
        # Нет текущего loop — можно использовать asyncio.run
        return asyncio.run(coro)
