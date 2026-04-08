"""
products/serializers.py

  - ProductDataSerializer  — для данных прямо из парсера (dataclass, не из БД)
  - SearchRequestSerializer — валидация входящего запроса поиска
  - SavedProductSerializer  — для товаров в избранном (из БД)
  - SaveProductInputSerializer — входные данные для POST /favourites/
"""

from __future__ import annotations

from rest_framework import serializers

from .models import SavedProduct

# Все допустимые унифицированные ключи сортировки.
# Каждый скрапер самостоятельно переводит их в нативные значения
# через свой SORT_MAPPING (см. wildberries.py / ozon.py).
SORTING_CHOICES = [
    "popular",    # по популярности (дефолт)
    "price_asc",  # цена ↑
    "price_desc", # цена ↓
    "rating",     # по рейтингу
    "new",        # новинки
    "discount",   # по скидке
    "reviews",    # по кол-ву отзывов
]


# ---------------------------------------------------------------------------
# Поиск
# ---------------------------------------------------------------------------

class ProductDataSerializer(serializers.Serializer):
    """Сериализует результат парсинга (ProductData dataclass). В БД не пишем."""

    marketplace = serializers.CharField()
    external_id = serializers.CharField()
    article = serializers.CharField(allow_blank=True)
    title = serializers.CharField()
    brand = serializers.CharField(allow_blank=True)
    price = serializers.FloatField(allow_null=True)
    original_price = serializers.FloatField(allow_null=True)
    discount_percent = serializers.SerializerMethodField()
    rating = serializers.FloatField(allow_null=True)
    reviews_count = serializers.IntegerField()
    in_stock = serializers.BooleanField()
    delivery_days = serializers.IntegerField(allow_null=True)
    url = serializers.CharField()
    image_url = serializers.CharField(allow_blank=True)
    category = serializers.CharField(allow_blank=True)
    attributes = serializers.DictField()

    def get_discount_percent(self, obj) -> float | None:
        price = obj.price
        orig = obj.original_price
        if price and orig and orig > 0:
            return round((1 - price / orig) * 100, 1)
        return None


class SearchRequestSerializer(serializers.Serializer):
    """Валидация входящего запроса для POST /api/v1/search/"""

    MARKETPLACE_CHOICES = ["wb", "ozon"]
    SORT_BY_CHOICES = ["price", "rating", "delivery_days", "title"]
    SORT_ORDER_CHOICES = ["asc", "desc"]

    query = serializers.CharField(
        allow_blank=False,
        help_text="Поисковый запрос, например 'iphone 15'",
    )
    marketplaces = serializers.ListField(
        child=serializers.ChoiceField(choices=MARKETPLACE_CHOICES),
        required=False,
        allow_null=True,
        default=None,
        help_text="Список маркетплейсов: ['wb', 'ozon']. По умолчанию — оба.",
    )

    # --- Пагинация ---
    page = serializers.IntegerField(
        required=False,
        default=1,
        min_value=1,
        help_text="Номер страницы выдачи маркетплейса (начиная с 1).",
    )

    # --- Нативная сортировка маркетплейса ---
    sorting = serializers.ChoiceField(
        choices=SORTING_CHOICES,
        required=False,
        allow_null=True,
        default=None,
        help_text=(
            "Нативная сортировка маркетплейса: "
            "popular | price_asc | price_desc | rating | new | discount | reviews. "
            "Применяется на стороне API маркетплейса, до возврата данных."
        ),
    )

    # --- Геолокация (влияет на WB: цены, наличие, сроки доставки) ---
    # Три взаимоисключающих способа передать регион (приоритет: dest > lat/lon > дефолт):
    #   1. dest       — готовый WB dest-код (если знаете его напрямую)
    #   2. lat + lon  — координаты; бэкенд сам вызовет WB geo API
    #   3. ничего     — используется DEFAULT_DEST (Иркутск)
    dest = serializers.IntegerField(
        required=False,
        allow_null=True,
        default=None,
        help_text=(
            "WB dest-код региона (напр. -5827722 для Иркутска). "
            "Если не указан, используются latitude+longitude или дефолт (Иркутск)."
        ),
    )
    latitude = serializers.FloatField(
        required=False,
        allow_null=True,
        default=None,
        min_value=-90.0,
        max_value=90.0,
        help_text="Широта для определения региона WB.",
    )
    longitude = serializers.FloatField(
        required=False,
        allow_null=True,
        default=None,
        min_value=-180.0,
        max_value=180.0,
        help_text="Долгота для определения региона WB.",
    )
    address = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        max_length=256,
        help_text="Человекочитаемый адрес (необязательно, только подсказка для WB geo API).",
    )

    # --- Клиентская сортировка (постобработка в памяти) ---
    sort_by = serializers.ChoiceField(
        choices=SORT_BY_CHOICES,
        required=False,
        allow_null=True,
        default=None,
        help_text="Поле для клиентской сортировки результатов: price | rating | delivery_days | title",
    )
    sort_order = serializers.ChoiceField(
        choices=SORT_ORDER_CHOICES,
        required=False,
        default="asc",
        help_text="Направление клиентской сортировки: asc | desc",
    )

    # --- Фильтры ---
    min_price = serializers.DecimalField(
        required=False,
        allow_null=True,
        default=None,
        max_digits=12,
        decimal_places=2,
        min_value=0,
    )
    max_price = serializers.DecimalField(
        required=False,
        allow_null=True,
        default=None,
        max_digits=12,
        decimal_places=2,
        min_value=0,
    )
    min_rating = serializers.FloatField(
        required=False,
        allow_null=True,
        default=None,
        min_value=0.0,
        max_value=5.0,
    )
    max_delivery = serializers.IntegerField(
        required=False,
        allow_null=True,
        default=None,
        min_value=0,
    )
    in_stock = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Только товары в наличии.",
    )

    def validate_query(self, value: str) -> str:
        return value.strip()

    def validate(self, attrs):
        min_price = attrs.get("min_price")
        max_price = attrs.get("max_price")
        if min_price is not None and max_price is not None and min_price > max_price:
            raise serializers.ValidationError(
                {"max_price": "max_price должен быть больше или равен min_price."}
            )

        # Если передана только одна из координат — ошибка
        lat = attrs.get("latitude")
        lon = attrs.get("longitude")
        if (lat is None) != (lon is None):
            raise serializers.ValidationError(
                {"latitude": "latitude и longitude должны передаваться вместе."}
            )

        return attrs


# ---------------------------------------------------------------------------
# Избранное
# ---------------------------------------------------------------------------

class SavedProductSerializer(serializers.ModelSerializer):
    """Товар в избранном — читается из БД."""

    discount_percent = serializers.SerializerMethodField()

    class Meta:
        model = SavedProduct
        fields = [
            "id", "marketplace", "external_id", "article",
            "title", "brand",
            "price", "original_price", "discount_percent",
            "rating", "reviews_count",
            "in_stock", "delivery_days",
            "url", "image_url", "category", "attributes",
            "saved_at",
        ]
        read_only_fields = ["id", "saved_at"]

    def get_discount_percent(self, obj) -> float | None:
        if obj.original_price and obj.price and obj.original_price > 0:
            return round((1 - float(obj.price) / float(obj.original_price)) * 100, 1)
        return None


class SaveProductInputSerializer(serializers.Serializer):
    """Входные данные для POST /api/v1/favourites/."""

    marketplace = serializers.ChoiceField(choices=["wildberries", "ozon"])
    external_id = serializers.CharField(max_length=64)
    article = serializers.CharField(max_length=128, allow_blank=True, default="")
    title = serializers.CharField(max_length=512)
    brand = serializers.CharField(max_length=256, allow_blank=True, default="")
    price = serializers.FloatField(allow_null=True, required=False)
    original_price = serializers.FloatField(allow_null=True, required=False)
    rating = serializers.FloatField(allow_null=True, required=False, min_value=0, max_value=5)
    reviews_count = serializers.IntegerField(default=0, min_value=0)
    in_stock = serializers.BooleanField(default=True)
    delivery_days = serializers.IntegerField(allow_null=True, required=False, min_value=0)
    url = serializers.URLField(max_length=1024)
    image_url = serializers.URLField(max_length=1024, allow_blank=True, default="")
    category = serializers.CharField(max_length=256, allow_blank=True, default="")
    attributes = serializers.DictField(default=dict)
