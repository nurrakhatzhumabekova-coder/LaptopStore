from django.conf import settings
from django.db import models


class Brand(models.Model):
    name = models.CharField("Бренд", max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField("Категория", max_length=100)  # Игровые, Офисные, Ультрабуки
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Laptop(models.Model):
    title = models.CharField("Название", max_length=255)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="laptops")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="laptops")

    processor = models.CharField("Процессор", max_length=100)
    ram_gb = models.PositiveIntegerField("ОЗУ (ГБ)")
    storage_gb = models.PositiveIntegerField("SSD (ГБ)")
    graphics_card = models.CharField("Видеокарта", max_length=100)
    price = models.DecimalField("Цена", max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField("В наличии", default=0)
    is_available = models.BooleanField("Доступен", default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.brand.name} {self.title}"


# Корзина пользователя
class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart")
    created_at = models.DateTimeField(auto_now_add=True)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    laptop = models.ForeignKey(Laptop, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField("Количество", default=1)


# Заказ с ManyToMany связью через промежуточную модель
class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Ожидает оплаты'),
        ('paid', 'Оплачен'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    items = models.ManyToManyField(Laptop, through='OrderItem')
    total_price = models.DecimalField("Итоговая сумма", max_digits=10, decimal_places=2)
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    laptop = models.ForeignKey(Laptop, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)