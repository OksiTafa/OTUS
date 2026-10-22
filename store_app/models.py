from decimal import Decimal, ROUND_HALF_UP

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


# Create your models here.
class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='products')
    discount = models.IntegerField(default=0,
                                   validators=[MinValueValidator(0), MaxValueValidator(100)],
                                   help_text='Скидка в процентах (0–100)')

    @property
    def final_price(self):
        """Цена со скидкой: discount — процент от цены"""
        if not self.discount:
            return self.price
        final = self.price * (100 - self.discount) / 100
        return final.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name
