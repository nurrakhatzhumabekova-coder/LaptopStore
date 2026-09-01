from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

# Импортируем ProductDetailView
from main.views import ProductDetailView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # ✅ ГЛАВНАЯ СТРАНИЦА
    path('', TemplateView.as_view(template_name='index.html'), name='home'),

    # ✅ СТРАНИЦА ВХОДА
    path('login/', TemplateView.as_view(template_name='login.html'), name='login'),

    # ✅ СТРАНИЦА ТОВАРА
    path('product/<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),

    # API
    path('api/v1/', include('users.urls')),
    path('api/v1/', include('main.urls')),

    # JWT
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # Swagger
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)