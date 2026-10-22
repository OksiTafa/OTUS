from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from store_app.models import Product, Category
from .forms import ProductModelForm

LATEST_PRODUCTS_COUNT = 4  # сколько последних товаров показывать на главной


# Create your views here.
def index(request):
    """Главная страница: категории и последние добавленные товары"""
    context = {
        'categories': Category.objects.all(),
        'products': Product.objects.order_by('-created_at', '-pk')[:LATEST_PRODUCTS_COUNT],
    }
    return render(request, 'store_app/index.html', context=context)


def about(request):
    """Страница о нас."""
    return render(request, 'store_app/about.html')


class ProductListView(ListView):
    """Каталог: список товаров, сгруппированных по категориям"""
    model = Product
    template_name = 'store_app/catalog.html'
    context_object_name = 'catalog'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        categories = Category.objects.prefetch_related('products').all()
        category_id = self.request.GET.get('category')  # фильтр из ссылки на главной
        if category_id and category_id.isdigit():
            categories = categories.filter(pk=category_id)
        context['categories'] = categories
        return context


class ProductDetailView(DetailView):
    """Товар"""
    model = Product
    template_name = 'store_app/product_detail.html'
    pk_url_kwarg = 'product_id'


class ProductCreateView(CreateView):
    """Добавление нового товара"""
    model = Product
    form_class = ProductModelForm
    template_name = 'store_app/product_form.html'
    success_url = reverse_lazy('catalog')
    extra_context = {'title': 'Добавление товара'}


class ProductUpdateView(UpdateView):
    """Редактирование товара"""
    model = Product
    form_class = ProductModelForm
    template_name = 'store_app/product_form.html'
    pk_url_kwarg = 'product_id'
    extra_context = {'title': 'Редактирование товара'}

    def get_success_url(self):
        return reverse_lazy('product', kwargs={'product_id': self.object.pk})


class ProductDeleteView(DeleteView):
    """Удаление товара (с подтверждением)"""
    model = Product
    template_name = 'store_app/product_confirm_delete.html'
    pk_url_kwarg = 'product_id'
    success_url = reverse_lazy('catalog')
