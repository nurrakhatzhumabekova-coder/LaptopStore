from rest_framework import serializers
from .models import Category, Product, Order, OrderItem, Review
from django.db.models import Q


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Review
        fields = ('id', 'user', 'user_name', 'rating', 'text', 'created_at')
        read_only_fields = ('user', 'created_at')


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description', 'icon', 'product_count', 'created_at')


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    final_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    reviews_count = serializers.IntegerField(read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'slug', 'category', 'category_name',
            'brand', 'model', 'description', 'price', 'discount_price',
            'final_price', 'stock', 'image', 'image_url', 'specifications',
            'is_active', 'is_featured', 'average_rating', 'reviews_count',
            'created_at', 'updated_at'
        )

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'product_name', 'quantity', 'price', 'product_price')


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    item_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Order
        fields = (
            'id', 'user', 'products', 'items', 'total_price',
            'status', 'shipping_address', 'phone', 'notes',
            'item_count', 'created_at', 'updated_at'
        )
        read_only_fields = ('user', 'total_price', 'created_at', 'updated_at')


class OrderCreateSerializer(serializers.Serializer):
    product_ids = serializers.ListField(child=serializers.IntegerField())
    quantities = serializers.ListField(child=serializers.IntegerField(min_value=1))
    shipping_address = serializers.CharField()
    phone = serializers.CharField()
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if len(attrs['product_ids']) != len(attrs['quantities']):
            raise serializers.ValidationError("Количество товаров не совпадает с количеством позиций")
        return attrs