import pytest
from decimal import Decimal
from store_app.models import Product, Category


@pytest.fixture
def category():
    return Category.objects.create(name="Электроника", description="Техника и гаджеты")


@pytest.fixture
def product(category):
    return Product.objects.create(name="Смартфон",
                                  description="Современный смартфон с большим экраном",
                                  price=Decimal("25000.00"),
                                  category=category)


@pytest.fixture
def form_data(category):
    return {"name": "Ноутбук игровой",
            "description": "Мощный компьютер для работы и игр",
            "price": "80000",
            "category": category.pk}
