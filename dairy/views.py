from django.shortcuts import render
from gaytri_farm_app.utils import wrap_response
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from gaytri_farm_app.custom_permission import IsVerified, CustomerOrAdminPermission ,AdminUserPermission,CustomerPermission
from .models import *
from .serializers import *
from rest_framework.response import Response

# Create your views here.
# Product Views for add product , update product , delete product , get product details and list of products

class ProductDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated(), IsVerified(),CustomerOrAdminPermission()]
        else:
            return [IsAuthenticated(), IsVerified(), AdminUserPermission()]
        
    def get_object(self, pk):
        try:
            return Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return None
        
    def get(self, request, pk=None):
        if pk:  # If pk is provided, return a single product
            product = self.get_object(pk)
            if not product:
                return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
            serializer = ProductSerializer(product)
            return Response(serializer.data)
    
        # Otherwise, return all products
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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

# for Order Views for create order , update order , delete order , get order details and l
    
class OrderAPIView(APIView):
    permission_classes = [IsAuthenticated, CustomerPermission]

    def get_object(self, order_id):
        try:
            return Order.objects.get(order_id=order_id, customer=self.request.user)
        except Order.DoesNotExist:
            return None

    def get(self, request, order_id=None):
        if order_id:
            order = self.get_object(order_id)
            if not order:
                return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
            return Response(OrderSerializer(order).data)
        
        orders = Order.objects.filter(customer=request.user)
        return Response(OrderSerializer(orders, many=True).data)

    def post(self, request):
        serializer = OrderSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, order_id):
        order = self.get_object(order_id)
        if not order:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = OrderSerializer(order, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            quantity = serializer.validated_data.get('quantity', order.quantity)
            product = serializer.validated_data.get('product', order.product)
            serializer.save(total_price=product.price * quantity)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, order_id):
        order = self.get_object(order_id)
        if not order:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)  # No message body for 204
