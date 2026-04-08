"""
parsing/scrapers/ozon.py

Парсер Ozon. Принимает dest для совместимости с BaseScraper,
но не использует его — у Ozon своя геолокация через cookies/IP.
"""

from __future__ import annotations

import html
import json
import logging
import re
from typing import Optional

from curl_cffi.requests import Session

from .base import BaseScraper, ProductData

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "x-o3-app-name": "ozon-front",
    "x-o3-app-version": "3.30.0",
}

_API_URL = "https://api.ozon.ru/composer-api.bx/page/json/v2"

# ---------------------------------------------------------------------------
# Mapping унифицированных ключей → нативные значения Ozon (sorting=)
# Подтверждено через реальные URL Ozon и сторонние скраперы (Apify).
# ---------------------------------------------------------------------------
SORT_MAPPING: dict[str, str] = {
    "popular":    "score",
    "price_asc":  "price",
    "price_desc": "price_desc",
    "rating":     "rating",
    "new":        "new",
    "discount":   "discount",
    "reviews":    "reviews",
}

_DEFAULT_SORT = "score"


class OzonScraper(BaseScraper):
    marketplace = "ozon"

    def _search(
        self,
        query: str,
        page: int = 1,
        sorting: Optional[str] = None,
        dest: Optional[int] = None,   # не используется Ozon, только для совместимости
    ) -> list[ProductData]:
        native_sort = SORT_MAPPING.get(sorting or "", _DEFAULT_SORT)
        page_param = f"&page={page}" if page > 1 else ""
        search_url = (
            f"/search/?text={query}"
            f"&layout_container=categorySearchMegapagination"
            f"&sorting={native_sort}"
            f"{page_param}"
        )

        logger.info("[Ozon] query=%r page=%d sorting=%s", query, page, native_sort)
        try:
            with Session(impersonate="chrome120") as session:
                resp = session.get(
                    _API_URL,
                    params={"url": search_url},
                    headers=_HEADERS,
                    timeout=15,
                )
            logger.info("[Ozon] HTTP %s — %d байт", resp.status_code, len(resp.content))
            resp.raise_for_status()
        except Exception as exc:
            logger.error("[Ozon] Ошибка запроса: %s", exc)
            return []

        try:
            data = resp.json()
        except Exception as exc:
            logger.error("[Ozon] Не удалось распарсить JSON: %s", exc)
            return []

        items = _extract_items(data)
        logger.warning("[Ozon] Товаров в виджете: %d", len(items))

        results: list[ProductData] = []
        for item in items:
            try:
                results.append(_parse_item(item, self.marketplace))
            except Exception as exc:
                logger.warning("[Ozon] Ошибка парсинга карточки: %s", exc)

        logger.info("[Ozon] Итого: %d", len(results))
        return results


# ---------------------------------------------------------------------------
# Внутренние функции (без изменений)
# ---------------------------------------------------------------------------

def _is_in_stock(item: dict) -> bool:
    add_btn = item.get("multiButton", {}).get("ozonButton", {}).get("addToCart", {})
    if not add_btn:
        return False
    max_items = add_btn.get("quantityButton", {}).get("maxItems", 0)
    in_cart = add_btn.get("inCartQuantity", 0)
    if max_items > 0 and in_cart < max_items:
        return True
    action = add_btn.get("actionButton", {}).get("common", {}).get("action", {})
    if action.get("id") == "addToCart":
        return True
    return False


def _extract_items(data: dict) -> list:
    for key, value in data.get("widgetStates", {}).items():
        if not key.startswith("tileGridDesktop"):
            continue
        try:
            widget = json.loads(value) if isinstance(value, str) else value
            items = widget.get("items", [])
            if items:
                return items
        except (json.JSONDecodeError, AttributeError) as exc:
            logger.warning("[Ozon] Ошибка парсинга виджета %s: %s", key, exc)
    return []


def _parse_item(item: dict, marketplace: str) -> ProductData:
    product_id = str(item.get("id", ""))
    action_link = item.get("action", {}).get("link", "")
    url = "https://www.ozon.ru" + action_link.split("?")[0] if action_link else ""

    image_url = _extract_image(item)
    delivery_str = _extract_delivery(item)

    title = ""
    price: Optional[float] = None
    original_price: Optional[float] = None
    rating: Optional[float] = None
    reviews_count = 0

    for state in item.get("mainState", []):
        t = state.get("type")

        if t == "priceV2":
            for p in state.get("priceV2", {}).get("price", []):
                style = p.get("textStyle", "")
                text = p.get("text", "")
                if style == "PRICE":
                    price = _parse_price(text)
                elif style == "ORIGINAL_PRICE":
                    original_price = _parse_price(text)

        elif t == "textAtom" and state.get("id") == "name":
            title = html.unescape(state.get("textAtom", {}).get("text", ""))

        elif t == "labelList":
            for label in state.get("labelList", {}).get("items", []):
                auto_id = label.get("testInfo", {}).get("automatizationId", "")
                text = label.get("title", "").strip()
                if auto_id == "tile-list-rating":
                    rating = _parse_float(text)
                elif auto_id == "tile-list-comments":
                    reviews_count = _parse_int(text)

    return ProductData(
        marketplace=marketplace,
        external_id=product_id,
        title=title,
        price=price,
        original_price=original_price,
        rating=rating,
        reviews_count=reviews_count,
        url=url,
        image_url=image_url,
        delivery_days=_parse_delivery(delivery_str),
        in_stock=_is_in_stock(item),
    )


def _extract_image(item: dict) -> str:
    for img in item.get("tileImage", {}).get("items", []):
        if img.get("type") == "image":
            return img.get("image", {}).get("link", "")
    return ""


def _extract_delivery(item: dict) -> str:
    btn = (
        item.get("multiButton", {})
        .get("ozonButton", {})
        .get("addToCart", {})
        .get("actionButton", {})
    )
    return btn.get("common", {}).get("action", {}).get("title", "") or btn.get("title", "")


def _parse_price(text: str) -> Optional[float]:
    cleaned = text.replace(",", ".").replace("\u2009", "").replace("\xa0", "")
    digits = re.sub(r"[^\d.]", "", cleaned)
    try:
        return float(digits) if digits else None
    except ValueError:
        return None


def _parse_float(text: str) -> Optional[float]:
    if m := re.search(r"[\d.,]+", text):
        try:
            return float(m.group().replace(",", "."))
        except ValueError:
            pass
    return None


def _parse_int(text: str) -> int:
    digits = "".join(c for c in text if c.isdigit())
    return int(digits) if digits else 0


def _parse_delivery(text: str) -> Optional[int]:
    if not text:
        return None
    lower = text.lower()
    if "сегодня" in lower:
        return 0
    if "завтра" in lower:
        return 1
    if m := re.search(r"(\d+)", lower):
        return int(m.group(1))
    return None
