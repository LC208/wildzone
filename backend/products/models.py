"""
products/models.py

Товары НЕ кэшируются в БД после парсинга — парсинг отдаёт данные напрямую в ответ.
В БД хранится только то, что авторизованный пользователь добавил в избранное.
Анонимные пользователи не могут сохранять товары.
"""
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

class SavedProduct(models.Model):
    """
    Товар в избранном у зарегистрированного пользователя.
    Поля дублируют данные парсера — snapshot на момент сохранения.
    """

    user           = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favourites")
    marketplace    = models.CharField(max_length=10, choices=[("wb", "Wildberries"), ("ozon", "Ozon")])
    external_id    = models.CharField(max_length=64)
    article        = models.CharField(max_length=128, blank=True)
    title          = models.CharField(max_length=512)
    brand          = models.CharField(max_length=256, blank=True)
    price          = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    original_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    rating         = models.FloatField(null=True, blank=True)
    reviews_count  = models.PositiveIntegerField(default=0)
    in_stock       = models.BooleanField(default=True)
    delivery_days  = models.PositiveSmallIntegerField(null=True, blank=True)
    url            = models.URLField(max_length=1024)
    image_url      = models.URLField(max_length=1024, blank=True)
    category       = models.CharField(max_length=256, blank=True)
    attributes     = models.JSONField(default=dict, blank=True)

    saved_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "marketplace", "external_id")
        ordering = ["-saved_at"]

    def __str__(self):
        return f"{self.user.username} / [{self.marketplace}] {self.title}"