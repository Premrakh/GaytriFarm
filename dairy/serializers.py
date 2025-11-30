# shop/serializers.py
from rest_framework import serializers
from .models import Product, Order

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class OrderCreateSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField(min_value=1,required=True)
    date = serializers.DateField(required=True)
    class Meta:
        model = Order
        fields = ['product', 'quantity','date']  

class CustomerOrderSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_id = serializers.CharField(source='product.id', read_only=True)
    class Meta:
        model = Order
        fields = "__all__"

class ManagerOrderSerializer(serializers.ModelSerializer):
    customer = serializers.CharField(source='customer.user_name', read_only=True)
    customer_mobile = serializers.CharField(source='customer.mobile', read_only=True)
    customer_address = serializers.CharField(source='customer.address', read_only=True)
    product = serializers.StringRelatedField()

    class Meta:
        model = Order
        fields = ["id","customer", "customer_mobile", "customer_address","delivery_staff",
                  "product","quantity","total_price","date","status"]


    
class CustomerBillDetailSerializer(serializers.Serializer):
    month = serializers.IntegerField()
    year = serializers.IntegerField()
    customer_id = serializers.IntegerField(required=False)

class BulkOrderSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField(required=True)
    type = serializers.ChoiceField(choices=[
            ('every_day', 'every_day'),
            ('alternate_day', 'alternate_day'),
            ('one_two_cycle', 'one_two_cycle'),
        ],
        required=True
    )

    class Meta:
        model = Order
        fields = ['product', 'quantity',  'type']