from django.contrib import admin
from django.contrib.admin import action

from .models import Product, Category


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
        """Применяет скидку 5% к выбранным товарам"""
        for product in queryset:
            product.discount = 5
            product.save()

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



    actions = (apply_discount,add_promo_to_description,remove_promo_from_description)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')


