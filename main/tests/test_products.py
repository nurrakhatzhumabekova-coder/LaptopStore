import pytest

@pytest.mark.django_db
def test_list_products(api_client, product):
    response = api_client.get('/api/v1/products/')
    assert response.status_code == 200
    assert len(response.data['results']) > 0

@pytest.mark.django_db
def test_filter_products(api_client, product):
    response = api_client.get('/api/v1/products/?brand=ASUS')
    assert response.status_code == 200
    assert len(response.data['results']) > 0

@pytest.mark.django_db
def test_search_products(api_client, product):
    response = api_client.get('/api/v1/products/?search=ROG')
    assert response.status_code == 200
    assert len(response.data['results']) > 0