# shop/serializers.py
from rest_framework import serializers
from .models import Product, Order
from user.models import User


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    customer = serializers.StringRelatedField(read_only=True)  # auto from logged-in user
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = Order
        fields = ['order_id', 'customer', 'product', 'quantity', 'total_price', 'order_date']
        read_only_fields = ['order_id', 'customer', 'total_price', 'order_date']

    def create(self, validated_data):
        request = self.context.get('request')
        customer = request.user  # custom User
        product = validated_data['product']
        quantity = validated_data.get('quantity', 1)

        # Auto-assign delivery staff from your model logic
        # Example: assign the user's delivery_staff if exists
        staff = customer.delivery_staff

        # Calculate total price from product
        total_price = product.price * quantity

        order = Order.objects.create(
            customer=customer,
            product=product,
            quantity=quantity,
            total_price=total_price,
            delivery_staff=staff
        )
        return order
    

