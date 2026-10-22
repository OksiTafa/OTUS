import pytest
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed, assertContains, assertNotContains
from store_app.models import Category


@pytest.mark.django_db
def test_base_template(client):
    response = client.get(reverse("index"))
    assertTemplateUsed(response, "store_app/index.html")
    assertTemplateUsed(response, "store_app/base.html")
    assertTemplateUsed(response, "store_app/include/menu.html")
    assertContains(response, "<title>Главная страница</title>", html=True)
    assertContains(response, reverse("product_add"))  # ссылки в меню
    assertContains(response, reverse("about"))


@pytest.mark.django_db
def test_about_template(client):
    response = client.get(reverse("about"))
    assertTemplateUsed(response, "store_app/about.html")
    assertTemplateUsed(response, "store_app/base.html")
    assertContains(response, "<title>О нас</title>", html=True)
    assertContains(response, "Добро пожаловать в наш магазин!")
    assertContains(response, reverse("catalog"))


@pytest.mark.django_db
def test_catalog_template(client, category, product):
    response = client.get(reverse("catalog"))
    assertTemplateUsed(response, "store_app/catalog.html")
    assertContains(response, category.name)
    assertContains(response, product.name)
    assertContains(response, "25000,00 руб.")  # локаль ru-ru: десятичная запятая
    assertContains(response, reverse("product", args=[product.pk]))

    product.discount = 5
    product.save()
    response = client.get(reverse("catalog"))
    assertContains(response, "-5%")
    assertContains(response, "text-decoration-line-through")
    assertContains(response, "23750,00 руб.")  # цена со скидкой 5%


@pytest.mark.django_db
def test_catalog_template_empty(client):
    response = client.get(reverse("catalog"))
    assertContains(response, "Категорий пока нет")

    Category.objects.create(name="Книги", description="Художественная литература")
    response = client.get(reverse("catalog"))
    assertContains(response, "В этой категории товаров пока нет")


@pytest.mark.django_db
def test_product_detail_template(client, product):
    response = client.get(reverse("product", args=[product.pk]))
    assertTemplateUsed(response, "store_app/product_detail.html")
    assertContains(response, f"<title>{product.name} - Магазин</title>", html=True)
    assertContains(response, product.description)
    assertContains(response, product.category.name)
    assertContains(response, reverse("product_edit", args=[product.pk]))
    assertContains(response, reverse("product_delete", args=[product.pk]))

    product.discount = 10
    product.save()
    response = client.get(reverse("product", args=[product.pk]))
    assertContains(response, "22500,00 руб.")  # цена со скидкой 10%
    assertContains(response, "-10%")


@pytest.mark.django_db
def test_index_template(client, category, product):
    response = client.get(reverse("index"))
    assertContains(response, category.name)
    assertContains(response, product.name)
    assertContains(response, f'{reverse("catalog")}?category={category.pk}')
    assertNotContains(response, "Категорий пока нет")
    assertNotContains(response, "Товаров пока нет")


@pytest.mark.django_db
def test_product_form_template(client, product):
    response = client.get(reverse("product_add"))
    assertTemplateUsed(response, "store_app/product_form.html")
    assertContains(response, "<h1>Добавление товара</h1>", html=True)
    assertContains(response, "csrfmiddlewaretoken")

    response = client.get(reverse("product_edit", args=[product.pk]))
    assertTemplateUsed(response, "store_app/product_form.html")
    assertContains(response, "<h1>Редактирование товара</h1>", html=True)
    assertContains(response, f'value="{product.name}"')  # форма заполнена данными товара


@pytest.mark.django_db
def test_product_confirm_delete_template(client, product):
    response = client.get(reverse("product_delete", args=[product.pk]))
    assertTemplateUsed(response, "store_app/product_confirm_delete.html")
    assertContains(response, f"Вы действительно хотите удалить товар «{product.name}»?")
    assertContains(response, "csrfmiddlewaretoken")
