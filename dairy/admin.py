from django.contrib import admin
from .models import Product, Order, UserBill


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'product', 'quantity', 'status','date')
    ordering = ('-date',)

@admin.register(UserBill)
class UserBillAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_product', 'total_amount')