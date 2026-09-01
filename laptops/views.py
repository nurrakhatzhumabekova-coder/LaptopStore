from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Brand, Category, Laptop
from .serializers import BrandSerializer, CategorySerializer, LaptopSerializer


class IsAdminOrReadOnly(permissions.BasePermission):
    """Читать могут все, изменять — только администраторы"""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class LaptopViewSet(viewsets.ModelViewSet):
    queryset = Laptop.objects.all().select_related('brand', 'category')
    serializer_class = LaptopSerializer
    permission_classes = [IsAdminOrReadOnly]

    # Фильтрация, поиск и сортировка
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['brand', 'category', 'ram_gb', 'storage_gb', 'is_available']
    search_fields = ['title', 'processor', 'graphics_card']
    ordering_fields = ['price', 'created_at']


class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [IsAdminOrReadOnly]


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Cart, CartItem, Order, OrderItem, Laptop
from .serializers import CartSerializer, CartItemSerializer, OrderSerializer


class IsOwner(permissions.BasePermission):
    """Доступ разрешен только владельцу объекта"""
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def get_object(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart

    @action(detail=False, methods=['post'])
    def add_item(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        laptop_id = request.data.get('laptop_id')
        quantity = int(request.data.get('quantity', 1))

        try:
            laptop = Laptop.objects.get(id=laptop_id)
        except Laptop.DoesNotExist:
            return Response({'error': 'Ноутбук не найден'}, status=status.HTTP_404_NOT_FOUND)

        item, created = CartItem.objects.get_or_create(cart=cart, laptop=laptop)
        if not created:
            item.quantity += quantity
        else:
            item.quantity = quantity
        item.save()

        return Response(CartSerializer(cart).data)


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        items = cart.items.all()

        if not items.exists():
            return Response({'error': 'Корзина пуста'}, status=status.HTTP_400_BAD_REQUEST)

        total_price = sum(item.laptop.price * item.quantity for item in items)
        order = Order.objects.create(user=request.user, total_price=total_price)

        for item in items:
            OrderItem.objects.create(
                order=order,
                laptop=item.laptop,
                quantity=item.quantity,
                price_at_purchase=item.laptop.price
            )

        items.delete() # Очищаем корзину после создания заказа
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)