import pytest
from store_app.forms import ProductModelForm


@pytest.mark.django_db
def test_valid_form(form_data):
    form = ProductModelForm(data=form_data)
    assert form.is_valid() is True
    product = form.save()
    assert product.pk is not None


@pytest.mark.django_db
def test_clean_name(form_data):
    form_data["name"] = "  Ноутбук    игровой  "
    form = ProductModelForm(data=form_data)
    assert form.is_valid() is True
    assert form.cleaned_data["name"] == "Ноутбук игровой"  # лишние пробелы убраны

    form_data["name"] = "     "
    form = ProductModelForm(data=form_data)
    assert form.is_valid() is False
    assert "name" in form.errors

    form_data["name"] = "Ноут"
    form = ProductModelForm(data=form_data)
    assert form.is_valid() is False
    assert "Название товара должно содержать минимум 5 символов" in form.errors["name"]

    form_data["name"] = "Ноутбук #1"
    form = ProductModelForm(data=form_data)
    assert form.is_valid() is False
    assert "Название не должно содержать специальные символы (!@#$%)" in form.errors["name"]


@pytest.mark.django_db
def test_clean_description(form_data):
    form_data["description"] = ""
    form = ProductModelForm(data=form_data)
    assert form.is_valid() is False
    assert "description" in form.errors

    form_data["description"] = "Хороший ноутбук"
    form = ProductModelForm(data=form_data)
    assert form.is_valid() is False
    assert "Описание должно быть более информативным (минимум 20 символов)" in form.errors["description"]


@pytest.mark.django_db
def test_clean_price(form_data):
    form_data["price"] = "-1"
    form = ProductModelForm(data=form_data)
    assert form.is_valid() is False
    assert "Цена не может быть отрицательной" in form.errors["price"]

    form_data["price"] = "1000001"
    form = ProductModelForm(data=form_data)
    assert form.is_valid() is False
    assert "Цена не должна превышать 1 000 000 рублей" in form.errors["price"]

    form_data["price"] = "0"
    form = ProductModelForm(data=form_data)
    assert form.is_valid() is True


@pytest.mark.django_db
def test_clean_name_in_description(form_data):
    form_data["description"] = "Ноутбук игровой с мощной видеокартой"
    form = ProductModelForm(data=form_data)
    assert form.is_valid() is False
    assert "Название не должно дублироваться в описании" in form.non_field_errors()


@pytest.mark.django_db
def test_required_fields():
    form = ProductModelForm(data={})
    assert form.is_valid() is False
    assert set(form.errors) == {"name", "description", "price", "category"}
