from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
import random
import string
from .serializers import (
    RegisterSerializer,
    VerifyCodeSerializer,
    ResendCodeSerializer,
    CustomTokenObtainPairSerializer,
    UserProfileSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
    LoginSerializer,
    LoginResponseSerializer,
    LogoutSerializer,
    LogoutResponseSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """Регистрация нового пользователя"""
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    @extend_schema(
        summary="Регистрация пользователя",
        description="Создание нового пользователя с отправкой кода верификации на email",
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(
                description="Пользователь успешно создан",
                response=RegisterSerializer
            ),
            400: OpenApiResponse(
                description="Ошибка валидации"
            )
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        user = serializer.save()
        self.send_verification(user)
        return user

    def send_verification(self, user):
        code = ''.join(random.choices(string.digits, k=6))
        user.verification_code = code
        user.save()

        if user.email:
            try:
                send_mail(
                    subject='Подтверждение регистрации',
                    message=f'Ваш код подтверждения: {code}\n\n'
                            f'Введите этот код для завершения регистрации.\n'
                            f'Код действителен в течение 15 минут.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Ошибка отправки email: {e}")


class VerifyCodeView(generics.GenericAPIView):
    """Верификация пользователя по коду"""
    permission_classes = [AllowAny]
    serializer_class = VerifyCodeSerializer

    @extend_schema(
        summary="Подтверждение кода верификации",
        description="Подтверждение регистрации с помощью 6-значного кода",
        request=VerifyCodeSerializer,
        responses={
            200: OpenApiResponse(
                description="Код успешно подтвержден",
                response={'message': 'Код верификации подтвержден ✅'}
            ),
            400: OpenApiResponse(
                description="Неверный код"
            )
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            {"message": "Код верификации подтвержден ✅"},
            status=status.HTTP_200_OK
        )


class CustomTokenObtainPairView(TokenObtainPairView):
    """Получение JWT токена с кастомными данными"""
    serializer_class = CustomTokenObtainPairSerializer

    @extend_schema(
        summary="Вход в систему (JWT)",
        description="Получение access и refresh токенов с дополнительными данными пользователя",
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(
                description="Успешный вход",
                response=LoginResponseSerializer,
                examples=[
                    OpenApiExample(
                        'Пример ответа',
                        value={
                            'access': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
                            'refresh': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
                            'user_id': 1,
                            'username': 'admin',
                            'email': 'admin@store.com',
                            'is_verified': True
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Ошибка входа"
            ),
            401: OpenApiResponse(
                description="Неверные учетные данные"
            )
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class LogoutView(generics.GenericAPIView):
    """Выход из системы (blacklist токена)"""
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    @extend_schema(
        summary="Выход из системы",
        description="Добавляет refresh токен в черный список, делая его недействительным",
        request=LogoutSerializer,
        responses={
            200: OpenApiResponse(
                description="Успешный выход",
                response=LogoutResponseSerializer
            ),
            400: OpenApiResponse(
                description="Ошибка при выходе"
            ),
            401: OpenApiResponse(
                description="Требуется аутентификация"
            )
        }
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            refresh_token = serializer.validated_data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {"message": "Вы успешно вышли из системы 👋"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Профиль пользователя"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    @extend_schema(
        summary="Получить профиль пользователя",
        description="Возвращает информацию о текущем авторизованном пользователе",
        responses={
            200: UserProfileSerializer,
            401: OpenApiResponse(description="Требуется аутентификация")
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Обновить профиль пользователя",
        description="Обновление данных текущего пользователя",
        request=UserProfileSerializer,
        responses={
            200: UserProfileSerializer,
            401: OpenApiResponse(description="Требуется аутентификация")
        }
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(
        summary="Частично обновить профиль",
        description="Частичное обновление данных пользователя",
        request=UserProfileSerializer,
        responses={
            200: UserProfileSerializer,
            401: OpenApiResponse(description="Требуется аутентификация")
        }
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def get_object(self):
        return self.request.user


class ResendCodeView(generics.GenericAPIView):
    """Повторная отправка кода верификации"""
    permission_classes = [AllowAny]
    serializer_class = ResendCodeSerializer

    @extend_schema(
        summary="Повторно отправить код верификации",
        description="Отправляет новый 6-значный код на email пользователя",
        request=ResendCodeSerializer,
        responses={
            200: OpenApiResponse(
                description="Новый код отправлен",
                response={'message': 'Новый код отправлен на вашу почту 📧'}
            ),
            404: OpenApiResponse(description="Пользователь не найден"),
            400: OpenApiResponse(description="Пользователь уже верифицирован")
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']
        try:
            user = User.objects.get(username=username)
            if user.is_verified:
                return Response(
                    {"error": "Пользователь уже верифицирован"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            code = ''.join(random.choices(string.digits, k=6))
            user.verification_code = code
            user.save()

            if user.email:
                send_mail(
                    subject='Новый код подтверждения',
                    message=f'Ваш новый код подтверждения: {code}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )

            return Response(
                {"message": "Новый код отправлен на вашу почту 📧"},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {"error": "Пользователь не найден"},
                status=status.HTTP_404_NOT_FOUND
            )


class PasswordResetView(generics.GenericAPIView):
    """Запрос на сброс пароля"""
    permission_classes = [AllowAny]
    serializer_class = PasswordResetSerializer

    @extend_schema(
        summary="Запрос на сброс пароля",
        description="Отправляет инструкции по сбросу пароля на email",
        request=PasswordResetSerializer,
        responses={
            200: OpenApiResponse(
                description="Инструкции отправлены",
                response={'message': 'Инструкции по сбросу пароля отправлены на вашу почту 📧'}
            ),
            404: OpenApiResponse(description="Пользователь не найден")
        }
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
            user.verification_code = token[:6]
            user.save()

            reset_link = f"http://localhost:8000/reset-password/{token}/"
            send_mail(
                subject='Сброс пароля',
                message=f'Перейдите по ссылке для сброса пароля: {reset_link}\n\n'
                        f'Или введите код: {token[:6]}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )

            return Response(
                {"message": "Инструкции по сбросу пароля отправлены на вашу почту 📧"},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {"error": "Пользователь с таким email не найден"},
                status=status.HTTP_404_NOT_FOUND
            )


class PasswordResetConfirmView(generics.GenericAPIView):
    """Подтверждение сброса пароля"""
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    @extend_schema(
        summary="Подтверждение сброса пароля",
        description="Устанавливает новый пароль после подтверждения кода",
        request=PasswordResetConfirmSerializer,
        responses={
            200: OpenApiResponse(
                description="Пароль успешно изменен",
                response={'message': 'Пароль успешно изменен ✅'}
            ),
            400: OpenApiResponse(description="Неверный код")
        }
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
        new_password = serializer.validated_data['new_password']

        try:
            user = User.objects.get(email=email, verification_code=code)
            user.set_password(new_password)
            user.verification_code = None
            user.save()

            return Response(
                {"message": "Пароль успешно изменен ✅"},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {"error": "Неверный код или email"},
                status=status.HTTP_400_BAD_REQUEST
            )