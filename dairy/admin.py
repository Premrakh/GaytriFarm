from django.contrib import admin
from .models import Product, Order, DistributorOrder


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'product', 'quantity', 'status','date')
    ordering = ('-date',)
    list_filter = ('customer', 'product', 'status','created')

@admin.register(DistributorOrder)
class DistributorOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'distributor', 'product', 'quantity', 'total_price','created')
    list_filter = ('distributor', 'product', 'created')