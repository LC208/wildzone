from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterView, MeView, ChangePasswordView

urlpatterns = [
    path("register/",        RegisterView.as_view(),        name="auth-register"),
    path("login/",           TokenObtainPairView.as_view(), name="auth-login"),
    path("token/refresh/",   TokenRefreshView.as_view(),    name="auth-token-refresh"),
    path("me/",              MeView.as_view(),               name="auth-me"),
    path("change-password/", ChangePasswordView.as_view(),  name="auth-change-password"),
    path("password-reset/",  include("django_rest_passwordreset.urls",
                                     namespace="password_reset")),
]