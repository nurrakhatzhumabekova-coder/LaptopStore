import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from main.models import Category, Product

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def auth_client(api_client):
    user = User.objects.create_user(
        username='testuser',
        email='test@test.com',
        password='testpass123',
        is_verified=True
    )
    response = api_client.post('/api/v1/auth/login/', {
        'username': 'testuser',
        'password': 'testpass123'
    })
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return api_client, user

@pytest.fixture
def category():
    return Category.objects.create(
        name='Игровые ноутбуки',
        slug='gaming-laptops'
    )

@pytest.fixture
def product(category):
    return Product.objects.create(
        name='ASUS ROG Strix G16',
        slug='asus-rog-strix-g16',
        category=category,
        brand='ASUS',
        model='G16',
        description='Мощный игровой ноутбук',
        price=1500.00,
        stock=10,
        is_active=True
    )