from django import forms
from .models import Product
from django.core.exceptions import ValidationError


class ProductModelForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name','description','price','category']
        labels = {
            'name' : 'Заголовок',
            'description' : 'Описание',
            'price' : 'Цена',
            'category' : 'Категория'
        }
        ''' для каждого поля указываем, как оно будет отображаться в HTML'''
        widgets = {
            'name' : forms.TextInput(attrs={'class':'form-control'}),
            'description' : forms.Textarea(attrs={'class':'form-control'}),
            'price' : forms.NumberInput(attrs={'class':'form-control'}),
            'category' : forms.Select(attrs={'class':'form-control'})
        }

    def clean_price(self):
        """ кастомная валидация для поля price """
        price = self.cleaned_data.get('price')
        if price is None:
            return price

        if price < 0:
            raise ValidationError('Цена не может быть отрицательной')

        if price > 1000000:
            self.add_error('price', 'Цена не должна превышать 1 000 000 рублей')

        return price

    def clean_name(self):
        """ кастомная валидация для поля name """
        name = self.cleaned_data.get('name')

        if name:
            name = ' '.join(name.split())  # очистка от лишних пробелов

        if not name:
            raise ValidationError('Название товара не должно быть пустым')

        if len(name) < 5:
            raise ValidationError('Название товара должно содержать минимум 5 символов')

        if len(name) > 255:  # максимальная длина поля в модели
            self.add_error('name', 'Название слишком длинное')

        if any(char in name for char in ['!', '@', '#', '$', '%']):
            self.add_error('name', 'Название не должно содержать специальные символы (!@#$%)')

        return name

    def clean_description(self):
        """ кастомная валидация для поля description """
        description = self.cleaned_data.get('description')
        if not description:
            raise ValidationError('Описание не должно быть пустым')

        if len(description) < 20:
            raise ValidationError('Описание должно быть более информативным (минимум 20 символов)')

        return description

    def clean(self):
        """ кастомная валидация для ВСЕХ полей формы """
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        description = cleaned_data.get('description')

        if name and description and name in description:
            raise ValidationError('Название не должно дублироваться в описании')

        return cleaned_data
