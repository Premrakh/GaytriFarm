from django.urls import path
from .views import (ProductDetailAPIView, ProductDetailAPIView, CustomerOrderView, ManageOrderAPI, ManageOrderAPI,
                     CustomerMonthlyBillView, MonthlyRevenueView,BulkOrderView,DeliveredOrdersCount
)

urlpatterns = [
    # Product API (Admin only)
    path('products/', ProductDetailAPIView.as_view()),
    path('products/<int:pk>/', ProductDetailAPIView.as_view()),
    # Order API (Customer only)
    path('customers_orders/', CustomerOrderView.as_view()),
    path('customers_orders/<int:pk>/', CustomerOrderView.as_view()),
    path('manage_orders/', ManageOrderAPI.as_view()),
    path('manage_orders/<int:pk>/', ManageOrderAPI.as_view()),
    # Monthly Bill API
    path('customer_monthly_bill/', CustomerMonthlyBillView.as_view()),
    path('revenue/', MonthlyRevenueView.as_view()),
    path('bulk_order/', BulkOrderView.as_view()),
    path('delivered_orders_count/', DeliveredOrdersCount.as_view()),

]
