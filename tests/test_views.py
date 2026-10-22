import pytest
from django.urls import reverse
from store_app.models import Product, Category
from store_app.views import LATEST_PRODUCTS_COUNT


@pytest.mark.django_db
def test_index(client, category):
    for i in range(LATEST_PRODUCTS_COUNT + 2):
        Product.objects.create(name=f"Товар {i}", description="Описание", price=100, category=category)

    response = client.get(reverse("index"))
    assert response.status_code == 200
    assert list(response.context["categories"]) == [category]
    products = list(response.context["products"])
    assert len(products) == LATEST_PRODUCTS_COUNT
    assert products[0].name == f"Товар {LATEST_PRODUCTS_COUNT + 1}"  # сначала новые


def test_about(client):
    response = client.get(reverse("about"))
    assert response.status_code == 200
    assert "Страница о нас" in response.content.decode()


@pytest.mark.django_db
def test_product_list(client, product):
    response = client.get(reverse("catalog"))
    assert response.status_code == 200
    assert "Смартфон" in response.content.decode()


@pytest.mark.django_db
def test_product_list_filter_by_category(client, category, product):
    other = Category.objects.create(name="Книги", description="Художественная литература")

    response = client.get(reverse("catalog"), {"category": other.pk})
    assert list(response.context["categories"]) == [other]

    response = client.get(reverse("catalog"), {"category": "abc"})  # неверный параметр игнорируется
    assert len(response.context["categories"]) == 2


@pytest.mark.django_db
def test_product_detail(client, product):
    response = client.get(reverse("product", args=[product.pk]))
    assert response.status_code == 200
    assert response.context["product"] == product

    response = client.get(reverse("product", args=[999]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_product_create(client, form_data):
    response = client.post(reverse("product_add"), form_data)
    assert response.status_code == 302
    assert response.url == reverse("catalog")
    assert Product.objects.filter(name="Ноутбук игровой").exists() is True

    # форма с ошибкой валидации не создаёт товар
    form_data["name"] = "Ноут"  # меньше 5 символов
    response = client.post(reverse("product_add"), form_data)
    assert response.status_code == 200
    assert Product.objects.count() == 1


@pytest.mark.django_db
def test_product_update(client, product, form_data):
    response = client.post(reverse("product_edit", args=[product.pk]), form_data)
    assert response.status_code == 302
    assert response.url == reverse("product", args=[product.pk])
    product.refresh_from_db()
    assert product.name == "Ноутбук игровой"


@pytest.mark.django_db
def test_product_delete(client, product):
    url = reverse("product_delete", args=[product.pk])
    assert client.get(url).status_code == 200  # страница подтверждения

    response = client.post(url)
    assert response.status_code == 302
    assert response.url == reverse("catalog")
    assert Product.objects.filter(pk=product.pk).exists() is False
