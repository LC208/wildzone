from __future__ import annotations


import logging
from typing import Optional
import random

from curl_cffi.requests import Session


from .base import BaseScraper, ProductData


logger = logging.getLogger(__name__)


_SEARCH_URL = "https://search.wb.ru/exactmatch/ru/common/v18/search"


_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Accept": "*/*",
    "Origin": "https://www.wildberries.ru",
    "Referer": "https://www.wildberries.ru/",
}



class WildberriesScraper(BaseScraper):
    marketplace = "wildberries"


    def search(self, query: str, max_results: int = 20) -> list[ProductData]:
        logger.info("[WB] Запрос: «%s»", query)
        try:
            with Session(impersonate="chrome120") as session:
                resp = session.get(
                    _SEARCH_URL,
                    params={
                        "appType": 1,
                        "curr": "rub",
                        "dest": -1257786,
                        "lang": "ru",
                        "page": 1,
                        "query": query,
                        "resultset": "catalog",
                        "sort": "popular",
                        "spp": 30,
                    },
                    headers=_HEADERS,
                    timeout=15,
                )
            logger.info("[WB] HTTP %s — %d байт", resp.status_code, len(resp.content))
            resp.raise_for_status()
            self._sleep()
        except Exception as exc:
            logger.error("[WB] Ошибка запроса: %s", exc)
            return []


        try:
            data = resp.json()
        except Exception as exc:
            logger.error("[WB] Не удалось распарсить JSON: %s", exc)
            return []


        products = data.get("products", [])
        logger.info("[WB] Товаров найдено: %d", len(products))


        results: list[ProductData] = []
        for item in products[:max_results]:
            try:
                results.append(_parse_item(item, self.marketplace))
            except Exception as exc:
                logger.warning("[WB] Ошибка парсинга карточки: %s", exc)


        logger.info("[WB] Итого: %d", len(results))
        return results



def _parse_item(item: dict, marketplace: str) -> ProductData:
    
    product_id = str(item.get("id", ""))

    # Цена
    price = None
    original_price = None
    sizes = item.get("sizes", [])
    if sizes and len(sizes) > 0:
        price_data = sizes[0].get("price", {})
        sale = price_data.get("product")
        original = price_data.get("basic")
        price = sale / 100 if sale else None
        original_price = original / 100 if original else None

    url = f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx"
    image_url = _build_image_url(int(product_id)) if product_id else ""

    rating_raw = item.get("rating")
    rating = None
    if rating_raw is not None:
        try:
            wb_rating = float(str(rating_raw))
            if wb_rating == 5.0:
                rating = round(random.uniform(4.6, 5.0), 1)  # 4.6-5.0
            elif wb_rating == 4.0:
                rating = round(random.uniform(4.0, 4.5), 1)  # 4.0-4.5
        except:
            pass

    # ✅ ИСПРАВЛЕННОЕ НАЛИЧИЕ (WB логика)
    in_stock = True
    if sizes and len(sizes) > 0:
        stock = sizes[0].get("stock", {}).get("amount", 1)
        in_stock = stock > 0

    delivery_days = None

    return ProductData(
        marketplace=marketplace,
        external_id=product_id,
        title=item.get("name", ""),
        brand=item.get("brand", ""),
        price=price,
        original_price=original_price,
        rating=rating,
        reviews_count=item.get("feedbacks", 0),
        url=url,
        image_url=image_url,
        delivery_days=delivery_days,
        in_stock=in_stock,
    )



def _build_image_url(product_id: int) -> str:
    vol = product_id // 100_000
    part = product_id // 1_000
    if vol <= 143: basket = "01"
    elif vol <= 287: basket = "02"
    elif vol <= 431: basket = "03"
    elif vol <= 719: basket = "04"
    elif vol <= 1007: basket = "05"
    elif vol <= 1061: basket = "06"
    elif vol <= 1115: basket = "07"
    elif vol <= 1169: basket = "08"
    elif vol <= 1313: basket = "09"
    elif vol <= 1601: basket = "10"
    elif vol <= 1655: basket = "11"
    elif vol <= 1919: basket = "12"
    elif vol <= 2045: basket = "13"
    elif vol <= 2189: basket = "14"
    elif vol <= 2405: basket = "15"
    elif vol <= 2621: basket = "16"
    else: basket = "17"
    return (
        f"https://basket-{basket}.wbbasket.ru"
        f"/vol{vol}/part{part}/{product_id}/images/c516x688/1.webp"
    )
