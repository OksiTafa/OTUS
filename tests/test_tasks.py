import pytest
from django.contrib.auth.models import User
from store_app.tasks import send_discount_mailing


@pytest.fixture
def subscribers():
    User.objects.create_user("anna", email="anna@example.com")
    User.objects.create_user("boris", email="boris@example.com")
    User.objects.create_user("no_email", email="")  # без адреса — пропускается
    User.objects.create_user("blocked", email="blocked@example.com", is_active=False)


@pytest.mark.django_db
def test_send_discount_mailing(subscribers, product, mailoutbox):
    product.discount = 5
    product.save()

    result = send_discount_mailing(product_ids=[product.pk])
    assert result == "Отправлено писем: 2, товаров в рассылке: 1"

    assert len(mailoutbox) == 2
    assert sorted(m.to[0] for m in mailoutbox) == ["anna@example.com", "boris@example.com"]
    message = mailoutbox[0]
    assert message.subject == "Скидка 5% на товары!"
    assert len(message.to) == 1  # каждому отдельное письмо, чужих адресов не видно
    assert "Смартфон: 25000.00 → 23750.00 руб. (-5%)" in message.body


@pytest.mark.django_db
def test_send_discount_mailing_nothing_to_send(product, mailoutbox):
    assert send_discount_mailing(product_ids=[product.pk]) == "Нет получателей для рассылки"
    assert send_discount_mailing(product_ids=[999]) == "Нет товаров для рассылки"
    assert len(mailoutbox) == 0
