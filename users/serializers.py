from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
import random
import string

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации"""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        help_text="Пароль (минимум 8 символов)"
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        help_text="Подтверждение пароля"
    )

    class Meta:
        model = User
        fields = (
            'username', 'email', 'phone', 'password',
            'password2', 'first_name', 'last_name'
        )
        extra_kwargs = {
            'username': {'help_text': 'Уникальное имя пользователя'},
            'email': {'help_text': 'Email для входа и верификации'},
            'phone': {'help_text': 'Номер телефона в формате +996700123456'},
            'first_name': {'help_text': 'Имя'},
            'last_name': {'help_text': 'Фамилия'},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})

        if attrs.get('email') and User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Пользователь с таким email уже существует"})

        if attrs.get('phone') and User.objects.filter(phone=attrs['phone']).exists():
            raise serializers.ValidationError({"phone": "Пользователь с таким телефоном уже существует"})

        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        user.verification_code = ''.join(random.choices(string.digits, k=6))
        user.save()
        return user


class VerifyCodeSerializer(serializers.Serializer):
    """Сериализатор для верификации"""
    username = serializers.CharField(help_text="Имя пользователя")
    code = serializers.CharField(max_length=6, help_text="Код верификации из 6 цифр")

    def validate(self, attrs):
        try:
            user = User.objects.get(username=attrs['username'])
            if user.verification_code == attrs['code']:
                user.is_verified = True
                user.verification_code = None
                user.save()
                return attrs
            raise serializers.ValidationError("Неверный код верификации")
        except User.DoesNotExist:
            raise serializers.ValidationError("Пользователь не найден")


class ResendCodeSerializer(serializers.Serializer):
    """Сериализатор для повторной отправки кода"""
    username = serializers.CharField(help_text="Имя пользователя")


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Кастомный сериализатор для JWT токена с дополнительными данными"""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Добавляем кастомные данные в токен
        token['username'] = user.username
        token['email'] = user.email
        token['is_verified'] = user.is_verified
        token['phone'] = user.phone if user.phone else ''
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        # Проверка верификации
        if not self.user.is_verified:
            raise serializers.ValidationError(
                "Пользователь не верифицирован. Подтвердите email или телефон."
            )

        # Добавляем дополнительные данные в ответ
        data['user_id'] = self.user.id
        data['username'] = self.user.username
        data['email'] = self.user.email
        data['is_verified'] = self.user.is_verified

        return data


class LoginSerializer(serializers.Serializer):
    """Сериализатор для входа (Swagger документация)"""
    username = serializers.CharField(help_text="Имя пользователя")
    password = serializers.CharField(write_only=True, help_text="Пароль")


class LoginResponseSerializer(serializers.Serializer):
    """Сериализатор ответа при входе (Swagger документация)"""
    access = serializers.CharField(help_text="JWT access токен")
    refresh = serializers.CharField(help_text="JWT refresh токен")
    user_id = serializers.IntegerField(help_text="ID пользователя")
    username = serializers.CharField(help_text="Имя пользователя")
    email = serializers.EmailField(help_text="Email пользователя")
    is_verified = serializers.BooleanField(help_text="Статус верификации")


class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор профиля пользователя"""

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'phone', 'first_name',
            'last_name', 'avatar', 'is_verified', 'created_at',
            'updated_at'
        )
        read_only_fields = ('id', 'is_verified', 'created_at', 'updated_at')


class PasswordResetSerializer(serializers.Serializer):
    """Сериализатор для запроса сброса пароля"""
    email = serializers.EmailField(help_text="Email пользователя")


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Сериализатор для подтверждения сброса пароля"""
    email = serializers.EmailField(help_text="Email пользователя")
    code = serializers.CharField(max_length=6, help_text="Код сброса")
    new_password = serializers.CharField(write_only=True, validators=[validate_password], help_text="Новый пароль")
    new_password2 = serializers.CharField(write_only=True, help_text="Подтверждение нового пароля")

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Пароли не совпадают"})
        return attrs


class LogoutSerializer(serializers.Serializer):
    """Сериализатор для выхода (Swagger документация)"""
    refresh = serializers.CharField(help_text="Refresh токен для добавления в черный список")


class LogoutResponseSerializer(serializers.Serializer):
    """Сериализатор ответа при выходе (Swagger документация)"""
    message = serializers.CharField(help_text="Сообщение о выходе")