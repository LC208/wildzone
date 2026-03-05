from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SearchView, FavouriteViewSet

router = DefaultRouter()
router.register("favourites", FavouriteViewSet, basename="favourite")

urlpatterns = [
    path("search/", SearchView.as_view(), name="search"),
    path("", include(router.urls)),
]
