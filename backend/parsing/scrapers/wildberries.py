from __future__ import annotations

import logging
import time
from typing import List, Dict, Optional

from curl_cffi import requests as curl_requests

from ..geo import DEFAULT_DEST
from .base import BaseScraper, ProductData


logger = logging.getLogger(__name__)


_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Accept": "*/*",
    "Origin": "https://www.wildberries.ru",
    "Referer": "https://www.wildberries.ru/",
}

# ---------------------------------------------------------------------------
# Mapping унифицированных ключей → нативные значения WB sort=
# Подтверждено через DevTools / публичные парсеры:
#   popular   → popular   (дефолт WB)
#   price_asc → priceup
#   price_desc→ pricedown
#   rating    → rate
#   new       → newly
# ---------------------------------------------------------------------------
SORT_MAPPING: dict[str, str] = {
    "popular":    "popular",
    "price_asc":  "priceup",
    "price_desc": "pricedown",
    "rating":     "rate",
    "new":        "newly",
}

_DEFAULT_SORT = "popular"


class WildberriesScraper(BaseScraper):
    marketplace = "wildberries"

    SEARCH_URL = "https://search.wb.ru/exactmatch/ru/common/v18/search"
    CDN_URL = "https://cdn.wbbasket.ru/api/v3/upstreams"

    def __init__(self) -> None:
        super().__init__()
        self._route_map: Optional[List[Dict]] = None

    # ----------------------------------
    # PUBLIC API
    # ----------------------------------
    def _search(
        self,
        query: str,
        page: int = 1,
        sorting: Optional[str] = None,
        dest: Optional[int] = None,
    ) -> list[ProductData]:
        """
        :param dest: Код региона WB (dest). Влияет на цену, наличие и срок доставки.
                     Берётся из geo.resolve_dest() или DEFAULT_DEST если не передан.
        """
        effective_dest = dest if dest is not None else DEFAULT_DEST
        products = self._wb_search(query, page=page, sorting=sorting, dest=effective_dest)
        route_map = self._get_route_map()

        results: list[ProductData] = []
        for p in products:
            try:
                nm_id = p["id"]
                price_data = p.get("sizes", [{}])[0].get("price", {})

                product = ProductData(
                    external_id=str(nm_id),
                    title=p.get("name", ""),
                    url=f"https://www.wildberries.ru/catalog/{nm_id}/detail.aspx",
                    marketplace=self.marketplace,
                    article=str(nm_id),
                    price=self._safe_price(price_data.get("product")),
                    original_price=self._safe_price(price_data.get("basic")),
                    brand=p.get("brand", ""),
                    rating=p.get("reviewRating"),
                    reviews_count=p.get("feedbacks", 0),
                    in_stock=p.get("totalQuantity", 0) > 0,
                    image_url=self._get_image(nm_id, route_map),
                    category=p.get("entity", ""),
                )
                results.append(product)
            except Exception:
                continue

        return results

    # ----------------------------------
    # WB API
    # ----------------------------------
    def _wb_search(
        self,
        query: str,
        page: int = 1,
        sorting: Optional[str] = None,
        dest: int = DEFAULT_DEST,
    ) -> List[Dict]:
        native_sort = SORT_MAPPING.get(sorting or "", _DEFAULT_SORT)

        params = {
            "appType": 1,
            "curr": "rub",
            "dest": dest,          # ← регион доставки
            "lang": "ru",
            "page": page,
            "query": query,
            "resultset": "catalog",
            "sort": native_sort,
            "spp": 30,
        }

        logger.debug("[WB] dest=%d, page=%d, sort=%s, query=%r", dest, page, native_sort, query)

        r = curl_requests.get(
            self.SEARCH_URL,
            params=params,
            impersonate="chrome110",
            timeout=10,
        )
        r.raise_for_status()
        return r.json().get("products", [])

    # ----------------------------------
    # CDN (basket)
    # ----------------------------------
    def _get_route_map(self) -> List[Dict]:
        if self._route_map:
            return self._route_map

        ts = int(time.time() * 1000)
        r = curl_requests.get(
            f"{self.CDN_URL}?t={ts}",
            impersonate="chrome110",
            timeout=5,
        )
        r.raise_for_status()
        data = r.json()
        self._route_map = data["origin"]["mediabasket_route_map"][0]["hosts"]
        return self._route_map

    def _find_host(self, vol: int, route_map: List[Dict]) -> Optional[str]:
        for entry in route_map:
            if entry["vol_range_from"] <= vol <= entry["vol_range_to"]:
                return entry["host"]
        return None

    def _get_image(self, nm_id: int, route_map: List[Dict]) -> str:
        vol = nm_id // 100000
        part = nm_id // 1000
        host = self._find_host(vol, route_map)
        if not host:
            return ""
        return f"https://{host}/vol{vol}/part{part}/{nm_id}/images/c516x688/1.webp"

    @staticmethod
    def _safe_price(value: Optional[int]) -> Optional[float]:
        if value is None:
            return None
        return value / 100
