from django.urls import path
from .views import index, catalog, product_detail, product_add, product_edit

urlpatterns = [
    path('', index, name='index'),
    path('catalog/', catalog, name='catalog'),
    path('catalog/<int:product_id>/', product_detail, name='product'),
    path('product/add/', product_add, name='product_add'),
    path('catalog/<int:product_id>/edit/', product_edit, name='product_edit'),
]
