"""
parsing/geo.py

Резолвер геопозиции для Wildberries.

WB определяет регион доставки через параметр dest (целое число).
Он влияет на:
  - наличие товара на складе
  - цену с учётом логистики
  - срок доставки

Как это работает на фронте WB:
  GET https://www.wildberries.ru/__internal/user-geo-data/get-geo-info
      ?currency=RUB&latitude=...&longitude=...&locale=ru&address=...
      &dt=0&currentLocale=ru&b2bMode=false&newClient=true

Ответ содержит поле xinfo: "appType=1&curr=rub&dest=-5827722&spp=30"
Из него и нужно извлечь dest.

Публичный API не требует авторизации.
"""

from __future__ import annotations

import logging
import re
from typing import Optional
from urllib.parse import urlencode

from curl_cffi import requests as curl_requests

logger = logging.getLogger(__name__)

# Дефолтный dest — Иркутск (используется WB как fallback для неизвестного региона)
DEFAULT_DEST: int = -5827722

_GEO_URL = (
    "https://www.wildberries.ru/__internal/user-geo-data/get-geo-info"
)

_GEO_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://www.wildberries.ru",
    "Referer": "https://www.wildberries.ru/",
}


def resolve_dest(
    latitude: float,
    longitude: float,
    address: str = "",
) -> int:
    """
    Получить WB dest-код для заданных координат.

    :param latitude:  Широта.
    :param longitude: Долгота.
    :param address:   Человекочитаемый адрес (необязательно, WB принимает
                      пустую строку — тогда определяет сам по координатам).
    :returns:         Целочисленный dest-код (отрицательный).
                      При ошибке возвращает DEFAULT_DEST.
    """
    return DEFAULT_DEST
    # params = {
    #     "currency": "RUB",
    #     "latitude": latitude,
    #     "longitude": longitude,
    #     "locale": "ru",
    #     "address": address,
    #     "dt": 0,
    #     "currentLocale": "ru",
    #     "b2bMode": "false",
    #     "newClient": "true",
    # }

    # try:
    #     resp = curl_requests.get(
    #         _GEO_URL,
    #         params=params,
    #         headers=_GEO_HEADERS,
    #         impersonate="chrome110",
    #         timeout=5,
    #     )
    #     resp.raise_for_status()
    #     data = resp.json()

    #     # xinfo = "appType=1&curr=rub&dest=-5827722&spp=30"
    #     xinfo: str = data.get("xinfo", "")
    #     dest = _extract_dest_from_xinfo(xinfo)
    #     if dest is not None:
    #         logger.debug(
    #             "[Geo] address=%r → dest=%d (lat=%.4f, lon=%.4f)",
    #             address or "auto",
    #             dest,
    #             latitude,
    #             longitude,
    #         )
    #         return dest

    #     logger.warning("[Geo] dest не найден в xinfo=%r, использую дефолт", xinfo)

    # except Exception as exc:
    #     logger.warning("[Geo] Не удалось получить dest: %s. Использую дефолт.", exc)

    


def _extract_dest_from_xinfo(xinfo: str) -> Optional[int]:
    """Извлечь числовое значение dest= из строки xinfo."""
    m = re.search(r"dest=(-?\d+)", xinfo)
    if m:
        return int(m.group(1))
    return None
