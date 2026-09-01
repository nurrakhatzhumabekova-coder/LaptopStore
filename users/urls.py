from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from .views import (
    RegisterView,
    VerifyCodeView,
    ResendCodeView,
    CustomTokenObtainPairView,
    UserProfileView,
    LogoutView,
    PasswordResetView,
    PasswordResetConfirmView,
)

urlpatterns = [
    # Аутентификация
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/verify/', VerifyCodeView.as_view(), name='verify'),
    path('auth/resend-code/', ResendCodeView.as_view(), name='resend-code'),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/verify-token/', TokenVerifyView.as_view(), name='token_verify'),

    # Профиль
    path('auth/profile/', UserProfileView.as_view(), name='profile'),

    # Сброс пароля
    path('auth/password-reset/', PasswordResetView.as_view(), name='password-reset'),
    path('auth/password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
]