from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (ProductDetailAPIView, ProductDetailAPIView, CustomerOrderView, ManageOrderAPI, ManageOrderAPI,
                     CustomerMonthlyBillView, MonthlyRevenueView,StartOrderView,DeliveredOrdersCount, DeleteOrderView, PauseOrderView,OrderCountView,
                     OrderHandlerView
)

# Create a router and register the ViewSet
router = DefaultRouter()
router.register(r'order_handler', OrderHandlerView, basename='order_handler')

urlpatterns = [
    # Product API (Admin only)
    path('products/', ProductDetailAPIView.as_view()),
    path('products/<int:pk>/', ProductDetailAPIView.as_view()),
    # Order API (Customer only)
    path('customers_orders/', CustomerOrderView.as_view()),
    path('customers_orders/<int:pk>/', CustomerOrderView.as_view()),
    
    path('manage_orders/', ManageOrderAPI.as_view()),
    path('manage_orders/<int:pk>/', ManageOrderAPI.as_view()),

    path('start_order/', StartOrderView.as_view()),
    path('pause_order/', PauseOrderView.as_view()),
    path('delete_order/', DeleteOrderView.as_view()),
    # Monthly Bill API
    path('customer_monthly_bill/', CustomerMonthlyBillView.as_view()),
    path('revenue/', MonthlyRevenueView.as_view()),
    path('delivered_orders_count/', DeliveredOrdersCount.as_view()),
    path('orders_count/', OrderCountView.as_view()),
]

# Include router URLs
urlpatterns += router.urls

