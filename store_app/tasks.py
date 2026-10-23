from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail, send_mass_mail
import time

from store_app.models import Product


@shared_task
def add(x, y):
    time.sleep(7)
    return x + y


@shared_task
def send_mail_task(rec_email, subject, message):
    """Фоновая задача для отправки уведомлений на email."""
    send_mail(
        subject=subject,
        message=message,
        recipient_list=[rec_email],
        from_email='admin@mail.ru',
    )
    return f"Email sent to {rec_email}"


@shared_task
def send_discount_mailing(product_ids):
    """Рассылка всем активным пользователям о товарах, получивших скидку."""
    products = Product.objects.filter(pk__in=product_ids).order_by('name')
    if not products:
        return 'Нет товаров для рассылки'

    recipients = (get_user_model().objects
                  .filter(is_active=True)
                  .exclude(email='')
                  .values_list('email', flat=True))
    if not recipients:
        return 'Нет получателей для рассылки'

    lines = [f'• {p.name}: {p.price} → {p.final_price} руб. (-{p.discount}%)' for p in products]
    subject = 'Скидка 5% на товары!'
    message = 'На эти товары действует скидка:\n\n' + '\n'.join(lines)

    # отдельное письмо каждому получателю, чтобы не показывать чужие адреса
    messages = [(subject, message, settings.DEFAULT_FROM_EMAIL, [email]) for email in recipients]
    sent = send_mass_mail(messages, fail_silently=False)
    return f'Отправлено писем: {sent}, товаров в рассылке: {len(products)}'
