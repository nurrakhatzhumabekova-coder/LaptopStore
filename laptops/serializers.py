from rest_framework import serializers
from .models import Brand, Category, Laptop, Cart, CartItem, Order, OrderItem


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class LaptopSerializer(serializers.ModelSerializer):
    brand_name = serializers.ReadOnlyField(source='brand.name')
    category_name = serializers.ReadOnlyField(source='category.name')

    class Meta:
        model = Laptop
        fields = '__all__'

from rest_framework import serializers
from .models import Cart, CartItem, Order, OrderItem, Laptop


class CartItemSerializer(serializers.ModelSerializer):
    laptop_title = serializers.ReadOnlyField(source='laptop.title')
    price = serializers.ReadOnlyField(source='laptop.price')
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ('id', 'laptop', 'laptop_title', 'price', 'quantity', 'total_price')

    def get_total_price(self, obj):
        return obj.laptop.price * obj.quantity


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    grand_total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ('id', 'user', 'items', 'grand_total')

    def get_grand_total(self, obj):
        return sum(item.laptop.price * item.quantity for item in obj.items.all())


class OrderItemSerializer(serializers.ModelSerializer):
    laptop_title = serializers.ReadOnlyField(source='laptop.title')

    class Meta:
        model = OrderItem
        fields = ('id', 'laptop', 'laptop_title', 'quantity', 'price_at_purchase')


class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(source='orderitem_set', many=True, read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'user', 'total_price', 'status', 'created_at', 'order_items')
        read_only_fields = ('user', 'total_price', 'status')