import pytest
from django.urls import reverse
from store_app.models import Product


def run_action(admin_client, action, products):
    """Запускает действие админки для выбранных товаров"""
    return admin_client.post(reverse("admin:store_app_product_changelist"),
                             {"action": action, "_selected_action": [p.pk for p in products]},
                             follow=True)


@pytest.mark.django_db
def test_product_changelist(admin_client, product):
    response = admin_client.get(reverse("admin:store_app_product_changelist"), {"q": "Смартфон"})
    assert response.status_code == 200
    assert product.name in response.content.decode()


@pytest.mark.django_db
def test_apply_discount(admin_client, product):
    run_action(admin_client, "apply_discount", [product])
    product.refresh_from_db()
    assert product.discount == 5


@pytest.mark.django_db
def test_add_promo_to_description(admin_client, product):
    response = run_action(admin_client, "add_promo_to_description", [product])
    product.refresh_from_db()
    assert product.description.startswith("🔥 Товар дня! ")
    assert "Промо добавлено к 1 товарам" in response.content.decode()

    # повторное действие не дублирует промо
    run_action(admin_client, "add_promo_to_description", [product])
    product.refresh_from_db()
    assert product.description.count("Товар дня!") == 1


@pytest.mark.django_db
def test_remove_promo_from_description(admin_client, category, product):
    other = Product.objects.create(name="Наушники", description="Беспроводные наушники",
                                   price=3000, category=category)
    run_action(admin_client, "add_promo_to_description", [product])

    response = run_action(admin_client, "remove_promo_from_description", [product, other])
    product.refresh_from_db()
    assert product.description == "Современный смартфон с большим экраном"
    assert "Промо убрано из 1 товаров" in response.content.decode()
