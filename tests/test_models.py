import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from store_app.models import Product, Category


@pytest.mark.django_db
def test_create_category(category):
    assert category.pk is not None
    assert Category.objects.count() == 1


@pytest.mark.django_db
def test_read_category(category):
    result = Category.objects.get(pk=category.pk)
    assert (result.name == "Электроника" and
            result.description == "Техника и гаджеты")
    assert str(result) == "Электроника"
    assert repr(result) == "Электроника"


@pytest.mark.django_db
def test_update_category(category):
    category.name = "Бытовая техника"
    category.save()
    assert Category.objects.get(pk=category.pk).name == "Бытовая техника"


@pytest.mark.django_db
def test_delete_category(category, product):
    category.delete()
    assert Category.objects.filter(pk=category.pk).exists() is False
    # товары категории удаляются вместе с ней (on_delete=CASCADE)
    assert Product.objects.count() == 0


@pytest.mark.django_db
def test_create_product(product):
    assert product.pk is not None
    assert product.created_at is not None
    assert product.discount == 0  # значение по умолчанию
    assert Product.objects.count() == 1


@pytest.mark.django_db
def test_read_product(category, product):
    result = Product.objects.get(pk=product.pk)
    assert (result.name == "Смартфон" and
            result.price == Decimal("25000.00") and
            result.category == category)
    assert result in category.products.all()
    assert str(result) == "Смартфон"
    assert repr(result) == "Смартфон"


@pytest.mark.django_db
def test_update_product(product):
    product.price = Decimal("19999.99")
    product.discount = 10
    product.save()
    result = Product.objects.get(pk=product.pk)
    assert result.price == Decimal("19999.99")
    assert result.discount == 10


@pytest.mark.django_db
def test_delete_product(category, product):
    product.delete()
    assert Product.objects.filter(pk=product.pk).exists() is False
    assert Category.objects.filter(pk=category.pk).exists() is True


@pytest.mark.django_db
def test_final_price(product):
    assert product.final_price == Decimal("25000.00")
    product.discount = 5  # скидка в процентах
    assert product.final_price == Decimal("23750.00")
    product.discount = 100
    assert product.final_price == Decimal("0.00")

    product.price = Decimal("999.99")
    product.discount = 15
    assert product.final_price == Decimal("849.99")  # округление до копеек


@pytest.mark.django_db
def test_discount_validation(product):
    product.discount = 101
    with pytest.raises(ValidationError):
        product.full_clean()

    product.discount = -1
    with pytest.raises(ValidationError):
        product.full_clean()
