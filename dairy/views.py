from django.shortcuts import render
from gaytri_farm_app.utils import wrap_response
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from .models import *
from .serializers import *
from rest_framework.response import Response
from gaytri_farm_app.custom_permission import (IsAdminUser, IsCustomerUser) 

# Create your views here.
# Product Views for add product , update product , delete product , get product details and list of products
class ProductListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    def get_object(self, pk):
        try:
            return Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return None

    def get(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProductSerializer(product)
        return Response(serializer.data)

    def patch(self, request, pk):
        """Partial update"""
        product = self.get_object(pk)
        if not product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProductSerializer(product, data=request.data, partial=True)  # partial update
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# shop/views_order.py
# for Order Views for create order , update order , delete order , get order details and list of orders

class OrderAPIView(APIView):
    permission_classes = [IsAuthenticated, IsCustomerUser]

    def get(self, request):
        # Only show orders for the logged-in customer
        orders = Order.objects.filter(customer=request.user)
        serializer = OrderSerializer(orders, many=True)
        # If you want to return only selected fields
        data = [
            {
                "customer": o.customer.user_name,
                "product": o.product.name,  # adjust if Product has different field
                "quantity": o.quantity
            } for o in orders
        ]
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = OrderSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            order = serializer.save()
            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, order_id):
        try:
            order = Order.objects.get(order_id=order_id, customer=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = OrderSerializer(order, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            # Recalculate total_price if quantity or product changed
            quantity = serializer.validated_data.get('quantity', order.quantity)
            product = serializer.validated_data.get('product', order.product)
            serializer.save(total_price=product.price * quantity)
            return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, order_id):
        try:
            order = Order.objects.get(order_id=order_id, customer=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        order.delete()
        return Response({"success": "Order deleted"}, status=status.HTTP_204_NO_CONTENT)