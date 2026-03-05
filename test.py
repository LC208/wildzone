"""
Тест парсера Ozon API — без Selenium, без Django.
Нужен только: pip install requests
"""
import html
import json
import re
import requests
from dataclasses import dataclass
from typing import Optional

QUERY       = "iphone 15"
MAX_RESULTS = 10

HEADERS = {
    "User-Agent":       "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "x-o3-app-name":    "ozon-front",
    "x-o3-app-version": "3.30.0",
}


@dataclass
class Product:
    id:             str
    title:          str
    price:          Optional[float]
    original_price: Optional[float]
    rating:         Optional[float]
    reviews_count:  int
    url:            str
    image_url:      str
    delivery:       str   # строка как отдаёт Ozon, например "14 марта" или "сегодня"


def search(query: str, max_results: int = 20) -> list:
    resp = requests.get(
        "https://api.ozon.ru/composer-api.bx/page/json/v2",
        params={"url": f"/search/?text={query}&layout_container=categorySearchMegapagination"},
        headers=HEADERS,
        timeout=15,
    )
    print(f"HTTP {resp.status_code} — {len(resp.content)} байт")
    resp.raise_for_status()

    data  = resp.json()
    items = _extract_items(data)
    print(f"Товаров в виджете: {len(items)}")
    return [_parse_item(item) for item in items[:max_results]]


def _extract_items(data: dict) -> list:
    for key, value in data.get("widgetStates", {}).items():
        if not key.startswith("tileGridDesktop"):
            continue
        try:
            widget = json.loads(value)
            items  = widget.get("items", [])
            if items:
                return items
        except (json.JSONDecodeError, AttributeError):
            continue
    return []


def _parse_item(item: dict) -> Product:
    product_id  = item.get("id", "")
    action_link = item.get("action", {}).get("link", "")
    url         = "https://www.ozon.ru" + action_link.split("?")[0] if action_link else ""

    # Изображение — первое из tileImage
    image_url = ""
    for img in item.get("tileImage", {}).get("items", []):
        if img.get("type") == "image":
            image_url = img.get("image", {}).get("link", "")
            break

    # Доставка — из multiButton → ozonButton → addToCart → actionButton → title
    delivery = (
        item
        .get("multiButton", {})
        .get("ozonButton", {})
        .get("addToCart", {})
        .get("actionButton", {})
        .get("common", {})
        .get("action", {})
        .get("title", "")
    )
    # Запасной вариант — title прямо в addToCart
    if not delivery:
        delivery = (
            item
            .get("multiButton", {})
            .get("ozonButton", {})
            .get("addToCart", {})
            .get("actionButton", {})
            .get("title", "")
        )

    title          = ""
    price          = None
    original_price = None
    rating         = None
    reviews_count  = 0

    for state in item.get("mainState", []):
        t = state.get("type")

        # Цена и зачёркнутая цена
        if t == "priceV2":
            for p in state.get("priceV2", {}).get("price", []):
                style = p.get("textStyle", "")
                text  = p.get("text", "")
                if style == "PRICE":
                    price = _parse_price(text)
                elif style == "ORIGINAL_PRICE":
                    original_price = _parse_price(text)

        # Название
        elif t == "textAtom" and state.get("id") == "name":
            title = html.unescape(state.get("textAtom", {}).get("text", ""))

        # Рейтинг и отзывы
        elif t == "labelList":
            for label in state.get("labelList", {}).get("items", []):
                auto_id = label.get("testInfo", {}).get("automatizationId", "")
                text    = label.get("title", "").strip()
                if auto_id == "tile-list-rating":
                    rating = _parse_float(text)
                elif auto_id == "tile-list-comments":
                    reviews_count = _parse_int(text)

    return Product(
        id=product_id, title=title, price=price,
        original_price=original_price, rating=rating,
        reviews_count=reviews_count, url=url,
        image_url=image_url, delivery=delivery,
    )


def _parse_price(text: str) -> Optional[float]:
    digits = re.sub(r"[^\d.]", "", text.replace(",", ".").replace("\u2009", "").replace("\xa0", ""))
    try:
        return float(digits)
    except ValueError:
        return None

def _parse_float(text: str) -> Optional[float]:
    m = re.search(r"[\d.,]+", text)
    try:
        return float(m.group().replace(",", ".")) if m else None
    except ValueError:
        return None

def _parse_int(text: str) -> int:
    digits = "".join(c for c in text if c.isdigit())
    return int(digits) if digits else 0


if __name__ == "__main__":
    print(f"\nПоиск: «{QUERY}» (max {MAX_RESULTS})\n")

    try:
        results = search(QUERY, MAX_RESULTS)
    except requests.HTTPError as e:
        print(f"Ошибка HTTP: {e}")
        raise SystemExit(1)
    except requests.ConnectionError:
        print("Нет соединения с ozon.ru")
        raise SystemExit(1)

    if not results:
        print("Товары не найдены — возможно изменилась структура API")
        raise SystemExit(1)

    print(f"\nРезультат ({len(results)} товаров):\n")
    for i, p in enumerate(results, 1):
        print(f"{i:2}. {p.title[:70]}")
        print(f"    цена={p.price} | было={p.original_price} | "
              f"рейтинг={p.rating} | отзывы={p.reviews_count} | доставка={p.delivery!r}")
        print(f"    {p.url}")
        print()

    out = "ozon_test_result.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump([p.__dict__ for p in results], f, ensure_ascii=False, indent=2)
    print(f"Сохранено в {out}")