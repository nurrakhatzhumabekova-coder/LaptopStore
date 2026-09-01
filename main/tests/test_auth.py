import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
def test_register_user(api_client):
    data = {
        'username': 'newuser',
        'email': 'new@test.com',
        'password': 'TestPass123!',
        'password2': 'TestPass123!'
    }
    response = api_client.post('/api/v1/auth/register/', data)
    assert response.status_code == 201
    assert User.objects.filter(username='newuser').exists()

@pytest.mark.django_db
def test_login_user(api_client):
    user = User.objects.create_user(
        username='testuser',
        password='testpass123',
        is_verified=True
    )
    response = api_client.post('/api/v1/auth/login/', {
        'username': 'testuser',
        'password': 'testpass123'
    })
    assert response.status_code == 200
    assert 'access' in response.data