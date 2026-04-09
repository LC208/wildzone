from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import AbstractUser


# User = get_user_model()


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)


class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="profile")
    dark_theme = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"Profile({self.user.username})"


@receiver(post_save, sender=CustomUser)
def create_or_save_user_profile(sender, instance, created: bool, **kwargs) -> None:
    """
    Один сигнал вместо двух:
    - при создании — создаём профиль;
    - при обновлении — сохраняем только если профиль уже существует
      (избегаем лишнего UPDATE при каждом save пользователя).
    """
    if created:
        UserProfile.objects.create(user=instance)
    elif hasattr(instance, "profile"):
        instance.profile.save()
