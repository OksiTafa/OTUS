from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse

from store_app.models import Product, Category
from .forms import ProductModelForm

# Create your views here.
def index(request):
    """Главная страница"""
    return render(request, 'store_app/index.html')

def catalog(request):
    """Каталог"""
    catalog1 = Product.objects.all()
    categories = Category.objects.prefetch_related('products').all()

    context = {
        'catalog' : catalog1,
        'categories': categories,
    }
    return render(request, 'store_app/catalog.html', context=context)

def product_detail(request, product_id):
    """Товар"""
    product = get_object_or_404(Product, id=product_id)

    context = {
        'product' : product,
        'name' : product.name,
        'description' : product.description,
        'price' : product.price,
        'created_at' : product.created_at,
        'category' : product.category,
        'discount' : product.discount,
        'final_price' : product.final_price,
    }
    return render(request, 'store_app/product_detail.html', context=context)


def product_add(request):
    """ Добавление нового товара """
    form_product = ProductModelForm()
    if request.method == 'POST':
        form_product = ProductModelForm(request.POST)
        if form_product.is_valid():
            form_product.save()
            return redirect('catalog')

    context = {
        'form': form_product,
        'title': 'Добавление товара'
    }
    return render(request, 'store_app/product_form.html', context=context)

def product_edit(request, product_id):
    """ Редактирование товара """
    product = get_object_or_404(Product, id=product_id)
    form_product = ProductModelForm(instance=product)
    if request.method == 'POST':
        form_product = ProductModelForm(request.POST, instance=product)
        if form_product.is_valid():
            form_product.save()
            return redirect('catalog')

    context = {
        'form': form_product,
        'title': 'Добавление товара'
    }
    return render(request, 'store_app/product_form.html', context=context)
