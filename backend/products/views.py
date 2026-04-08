"""
products/views.py

Два независимых слоя:

1. SearchView — запускает парсинг, возвращает результаты напрямую, ничего не пишет в БД.
   Входные данные валидируются через SearchRequestSerializer.
   Фильтрация и сортировка происходят в памяти.

2. FavouriteViewSet — CRUD избранного из БД.
   Только для авторизованных пользователей.
"""

from __future__ import annotations

from typing import Any

from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from parsing.service import run_search

from .models import SavedProduct
from .serializers import (
    ProductDataSerializer,
    SavedProductSerializer,
    SaveProductInputSerializer,
    SearchRequestSerializer,
)


class SearchView(APIView):
    """
    POST /api/v1/search/

    Выполняет поиск на маркетплейсах, применяет фильтры и сортировку в памяти.
    В БД ничего не сохраняется.
    """

    @extend_schema(
        request=SearchRequestSerializer,
        responses={200: ProductDataSerializer(many=True)},
        summary="Поиск товаров на маркетплейсах",
        description=(
            "Выполняет поиск по wb и/или ozon, применяет фильтры "
            "(цена, рейтинг, доставка, наличие) и сортировку в памяти. "
            "Данные в БД не сохраняются."
        ),
        tags=["Search"],
    )
    def post(self, request):
        # Валидация входных данных через сериализатор (вместо ручного .get + int())
        req_ser = SearchRequestSerializer(data=request.data)
        req_ser.is_valid(raise_exception=True)
        params = req_ser.validated_data

        items = run_search(
            params["query"],
            marketplaces=params.get("marketplaces"),
            page=params["page"],
            sorting=params.get("sorting"),
            dest=params.get("dest"),
            latitude=params.get("latitude"),
            longitude=params.get("longitude"),
            address=params.get("address", ""),
        )

        items = _apply_filters(items, params)

        if sort_by := params.get("sort_by"):
            items = _apply_sort(items, sort_by, params["sort_order"])

        return Response(ProductDataSerializer(items, many=True).data)


class FavouriteViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    GET    /api/v1/favourites/      — список избранного
    POST   /api/v1/favourites/      — сохранить товар
    DELETE /api/v1/favourites/{id}/ — удалить

    Только для авторизованных пользователей.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = SavedProductSerializer

    def get_queryset(self):
        return SavedProduct.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        input_ser = SaveProductInputSerializer(data=request.data)
        input_ser.is_valid(raise_exception=True)
        data = input_ser.validated_data

        # Выделяем lookup-поля отдельно от defaults, чтобы не дублировать их
        lookup = {
            "user": request.user,
            "marketplace": data["marketplace"],
            "external_id": data["external_id"],
        }
        defaults = {k: v for k, v in data.items() if k not in lookup}

        obj, created = SavedProduct.objects.get_or_create(**lookup, defaults=defaults)
        if not created:
            return Response({"detail": "Товар уже в избранном."}, status=status.HTTP_200_OK)
        return Response(SavedProductSerializer(obj).data, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Вспомогательные функции фильтрации/сортировки
# ---------------------------------------------------------------------------

def _apply_filters(items: list, params: dict[str, Any]) -> list:
    min_price = params.get("min_price")
    max_price = params.get("max_price")
    min_rating = params.get("min_rating")
    max_delivery = params.get("max_delivery")
    in_stock = params.get("in_stock") or None  # False → не фильтруем

    result = []
    for item in items:
        if min_price is not None and (item.price is None or item.price < float(min_price)):
            continue
        if max_price is not None and (item.price is None or item.price > float(max_price)):
            continue
        if min_rating is not None and (item.rating is None or item.rating < float(min_rating)):
            continue
        if max_delivery is not None and (item.delivery_days is None or item.delivery_days > int(max_delivery)):
            continue
        if in_stock is not None and item.in_stock != in_stock:
            continue
        result.append(item)

    return result


def _apply_sort(items: list, sort_by: str, sort_order: str) -> list:
    reverse = sort_order == "desc"
    key_map = {
        "price":         lambda x: (x.price is None, x.price or 0),
        "rating":        lambda x: (x.rating is None, x.rating or 0),
        "delivery_days": lambda x: (x.delivery_days is None, x.delivery_days or 9999),
        "title":         lambda x: (x.title or "").lower(),
    }
    if key_fn := key_map.get(sort_by):
        items = sorted(items, key=key_fn, reverse=reverse)
    return items
