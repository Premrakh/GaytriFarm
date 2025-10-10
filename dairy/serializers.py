# shop/serializers.py
from rest_framework import serializers
from .models import Product, Order
from user.models import User


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class OrderCreateSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField(min_value=1,required=True)
    class Meta:
        model = Order
        fields = ['product', 'quantity']  

class CustomerOrderSerializer(serializers.ModelSerializer):
    product = serializers.StringRelatedField()
    class Meta:
        model = Order
        fields = "__all__"

class ManagerOrderSerializer(serializers.ModelSerializer):
    customer = serializers.CharField(source='customer.user_name', read_only=True)
    customer_address = serializers.CharField(source='customer.address', read_only=True)
    product = serializers.StringRelatedField()

    class Meta:
        model = Order
        fields = ["id","customer","customer_address","delivery_staff",
                  "product","quantity","total_price","date","status"]