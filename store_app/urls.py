from django.urls import path
from .views import (
    index,
    about,
    ProductListView,
    ProductDetailView,
    ProductCreateView,
    ProductUpdateView,
    ProductDeleteView,
)

urlpatterns = [
    path('', index, name='index'),
    path('about/', about, name='about'),
    path('catalog/', ProductListView.as_view(), name='catalog'),
    path('catalog/<int:product_id>/', ProductDetailView.as_view(), name='product'),
    path('product/add/', ProductCreateView.as_view(), name='product_add'),
    path('catalog/<int:product_id>/edit/', ProductUpdateView.as_view(), name='product_edit'),
    path('catalog/<int:product_id>/delete/', ProductDeleteView.as_view(), name='product_delete'),
]
