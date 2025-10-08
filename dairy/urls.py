from django.urls import path
from .views import *


urlpatterns = [
    # Product API (Admin only)
    path('products/', ProductListCreateAPIView.as_view(), name='product-list-create'),
    path('products/<int:pk>/', ProductDetailAPIView.as_view(), name='product-detail'),
    # Order API (Customer only)
    path('orders/', OrderAPIView.as_view(), name='orders-api'),
    path('orders/<uuid:order_id>/', OrderAPIView.as_view(), name='orders-detail'),

]
