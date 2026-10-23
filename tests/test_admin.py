import pytest
from unittest.mock import patch
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
def test_apply_discount(admin_client, category, product, django_capture_on_commit_callbacks):
    discounted = Product.objects.create(name="Наушники", description="Беспроводные наушники",
                                        price=3000, discount=5, category=category)

    with patch("store_app.admin.send_discount_mailing.delay") as mailing:
        with django_capture_on_commit_callbacks(execute=True):
            response = run_action(admin_client, "apply_discount", [product, discounted])
    product.refresh_from_db()
    assert product.discount == 5
    # рассылка только по товару, у которого скидки ещё не было
    mailing.assert_called_once_with([product.pk])
    assert "Скидка добавлена к 1 товарам, рассылка запущена" in response.content.decode()

    # повторно скидка не добавляется и рассылка не запускается
    with patch("store_app.admin.send_discount_mailing.delay") as mailing:
        with django_capture_on_commit_callbacks(execute=True):
            response = run_action(admin_client, "apply_discount", [product])
    mailing.assert_not_called()
    assert "У выбранных товаров скидка 5% уже есть" in response.content.decode()


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
