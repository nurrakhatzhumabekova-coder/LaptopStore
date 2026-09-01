from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.db.models import Q, Count, Sum, F, Avg
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView
from .models import Category, Product, Order, OrderItem, Review
from .serializers import (
    CategorySerializer, ProductSerializer, OrderSerializer,
    OrderCreateSerializer, ReviewSerializer
)
from .permissions import IsOwner, IsAdminOrReadOnly, IsAuthenticatedAndVerified


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.annotate(product_count=Count('products'))
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'brand', 'is_featured', 'is_active']
    search_fields = ['name', 'brand', 'model', 'description']
    ordering_fields = ['price', 'final_price', 'created_at', 'name']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()

        # ИСПРАВЛЕНО: используем другое имя для аннотации
        queryset = queryset.annotate(
            avg_rating=Avg('reviews__rating'),
            rev_count=Count('reviews')
        )

        query = self.request.query_params.get('q', '')
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(brand__icontains=query) |
                Q(model__icontains=query) |
                Q(description__icontains=query)
            )

        price_min = self.request.query_params.get('price_min', '')
        price_max = self.request.query_params.get('price_max', '')
        if price_min:
            queryset = queryset.filter(price__gte=price_min)
        if price_max:
            queryset = queryset.filter(price__lte=price_max)

        return queryset


class ReviewViewSet(viewsets.ModelViewSet):
    """ViewSet для отзывов"""
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        product_id = self.request.query_params.get('product_id')
        if product_id:
            return Review.objects.filter(product_id=product_id)
        return Review.objects.all()

    def perform_create(self, serializer):
        product_id = self.request.data.get('product')
        product = get_object_or_404(Product, id=product_id)
        serializer.save(user=self.request.user, product=product)


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['created_at', 'total_price']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all().annotate(item_count=Count('items'))
        return Order.objects.filter(user=user).annotate(item_count=Count('items'))

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsOwner]
        elif self.action in ['cancel']:
            self.permission_classes = [IsAuthenticated, IsOwner]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product_ids = serializer.validated_data['product_ids']
        quantities = serializer.validated_data['quantities']

        products = Product.objects.filter(id__in=product_ids, is_active=True)
        if len(products) != len(product_ids):
            return Response(
                {"error": "Некоторые товары недоступны"},
                status=status.HTTP_400_BAD_REQUEST
            )

        for product, qty in zip(products, quantities):
            if product.stock < qty:
                return Response(
                    {"error": f"Недостаточно товара {product.name}. Доступно: {product.stock}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        total_price = sum([p.final_price * q for p, q in zip(products, quantities)])
        order = Order.objects.create(
            user=request.user,
            total_price=total_price,
            shipping_address=serializer.validated_data['shipping_address'],
            phone=serializer.validated_data['phone'],
            notes=serializer.validated_data.get('notes', '')
        )

        for product, qty in zip(products, quantities):
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=qty,
                price=product.final_price
            )
            product.stock -= qty
            product.save()

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, IsOwner])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.status not in ['pending', 'processing']:
            return Response(
                {"error": "Заказ нельзя отменить"},
                status=status.HTTP_400_BAD_REQUEST
            )
        order.status = 'cancelled'
        order.save()

        for item in order.items.all():
            item.product.stock += item.quantity
            item.product.save()

        return Response(OrderSerializer(order).data)

    @action(detail=False, methods=['get'])
    def my_orders(self, request):
        orders = self.get_queryset()
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        if not request.user.is_staff:
            return Response(
                {"error": "Только для администраторов"},
                status=status.HTTP_403_FORBIDDEN
            )

        stats = {
            'total_orders': Order.objects.count(),
            'pending': Order.objects.filter(status='pending').count(),
            'processing': Order.objects.filter(status='processing').count(),
            'shipped': Order.objects.filter(status='shipped').count(),
            'delivered': Order.objects.filter(status='delivered').count(),
            'cancelled': Order.objects.filter(status='cancelled').count(),
            'total_revenue': Order.objects.filter(
                status__in=['delivered', 'shipped']
            ).aggregate(total=Sum('total_price'))['total'] or 0,
        }
        return Response(stats)


class ProductDetailView(DetailView):
    model = Product
    template_name = 'product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        context['related_products'] = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(id=product.id)[:4]
        context['reviews'] = product.reviews.all().order_by('-created_at')
        return context