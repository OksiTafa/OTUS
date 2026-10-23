from django.contrib import admin, messages
from django.db import transaction
from .models import Product, Category
from .tasks import send_discount_mailing

DISCOUNT_PERCENT = 5


# Register your models here.
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'price', 'category', 'discount', 'created_at')
    ordering = ('category', 'name')
    list_filter = ('price', 'category')
    search_fields = ('name', 'description')
    search_help_text = 'Введите часть названия товара или описания для поиска'

    @admin.action(description="Добавить скидку 5%%")
    def apply_discount(self, request, queryset):
        """Применяет скидку 5% к выбранным товарам и запускает рассылку"""
        changed_ids = []
        for product in queryset:
            if product.discount != DISCOUNT_PERCENT:  # о старой скидке повторно не пишем
                product.discount = DISCOUNT_PERCENT
                product.save()
                changed_ids.append(product.pk)

        if changed_ids:
            # задача уходит в Celery только после сохранения изменений в БД
            transaction.on_commit(lambda: send_discount_mailing.delay(changed_ids))
            self.message_user(request, f'Скидка добавлена к {len(changed_ids)} товарам, рассылка запущена')
        else:
            self.message_user(request, 'У выбранных товаров скидка 5% уже есть', messages.WARNING)

    @admin.action(description="Убрать скидку")
    def remove_discount(self, request, queryset):
        """Убирает скидку у выбранных товаров"""
        count = queryset.exclude(discount=0).update(discount=0)
        if count:
            self.message_user(request, f'Скидка убрана у {count} товаров')
        else:
            self.message_user(request, 'У выбранных товаров нет скидки', messages.WARNING)

    @admin.action(description="Добавить 'Товар дня!' к описанию")
    def add_promo_to_description(self, request, queryset):
        for product in queryset:
            if 'Товар дня!' not in product.description:
                product.description = f'🔥 Товар дня! {product.description}'
                product.save()
        self.message_user(request, f'Промо добавлено к {queryset.count()} товарам')

    @admin.action(description="Убрать 'Товар дня!' из описания")
    def remove_promo_from_description(self, request, queryset):
        count = 0
        for product in queryset:
            if 'Товар дня!' in product.description:
                product.description = product.description.replace('🔥 Товар дня! ', '')
                product.description = product.description.replace('Товар дня! ', '')
                product.description = product.description.replace('Товар дня!', '')
                product.description = product.description.strip()
                product.save()
                count += 1
        self.message_user(request, f'Промо убрано из {count} товаров')

    actions = (apply_discount, remove_discount, add_promo_to_description, remove_promo_from_description)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
