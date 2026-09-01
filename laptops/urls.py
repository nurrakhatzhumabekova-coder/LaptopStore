from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LaptopViewSet, BrandViewSet, CategoryViewSet, CartViewSet, OrderViewSet

router = DefaultRouter()
router.register(r'laptops', LaptopViewSet, basename='laptop')
router.register(r'brands', BrandViewSet, basename='brand')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
    path('cart/', CartViewSet.as_view({'get': 'retrieve'}), name='cart-detail'),
    path('cart/add/', CartViewSet.as_view({'post': 'add_item'}), name='cart-add'),
]