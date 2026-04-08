"""
accounts/serializers.py
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model  = User
        fields = ["id", "username", "email", "password"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    dark_theme = serializers.BooleanField(source="profile.dark_theme", required=False)

    class Meta:
        model  = User
        fields = ["id", "username", "email", "first_name", "last_name", "dark_theme"]

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", {})

        # fallback: если значение пришло прямо
        if "dark_theme" in validated_data:
            profile_data["dark_theme"] = validated_data.pop("dark_theme")

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if profile_data:
            for attr, value in profile_data.items():
                setattr(instance.profile, attr, value)
            instance.profile.save()

        return instance


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])

    def validate_old_password(self, value):
        request = self.context.get("request")
        user = getattr(request, "user", None) or self.context.get("user")

        if user is None:
            raise serializers.ValidationError(
                "Сериализатор вызван без пользователя в контексте."
            )

        if not user.check_password(value):
            raise serializers.ValidationError("Неверный текущий пароль.")

        return value
