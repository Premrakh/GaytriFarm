from django.shortcuts import render
from gaytri_farm_app.utils import wrap_response
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from gaytri_farm_app.custom_permission import (
    IsVerified,  AdminUserPermission, CustomerPermission
)
from .models import *
from .serializers import *

# Product Views
class ProductDetailAPIView(APIView):
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated(), IsVerified()]
        else:
            return [IsAuthenticated(), IsVerified(), AdminUserPermission()]
        
    def get_object(self, pk):
        try:
            return Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return None
        
    def get(self, request, pk=None):
        if pk:
            product = self.get_object(pk)
            if not product:
                return wrap_response(
                    success=False,
                    code="PRODUCT_NOT_FOUND",
                    message="Product not found",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            serializer = ProductSerializer(product)
            return wrap_response(True, "Product fetched successfully", data=serializer.data, status_code=status.HTTP_200_OK)

        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return wrap_response(True, "Products fetched successfully", data=serializer.data,status_code=status.HTTP_200_OK)

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return wrap_response(True, "product_created", data=serializer.data, status_code=status.HTTP_201_CREATED)
        return wrap_response(False, "Product creation failed", errors=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return wrap_response(
                False, "PRODUCT_NOT_FOUND", message="Product not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        serializer = ProductSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return wrap_response(True, "product_updated", data=serializer.data,status_code=status.HTTP_200_OK)
        return wrap_response(False, "Product update failed", errors=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return wrap_response(
                False, "PRODUCT_NOT_FOUND", message="Product not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        product.delete()
        return wrap_response(True, "product_deleted", message="Product deleted successfully", status_code=status.HTTP_204_NO_CONTENT)


# Order Views
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
                return wrap_response(False, "Order not found", message="Order not found", status_code=status.HTTP_404_NOT_FOUND)
            return wrap_response(True, "Order fetched successfully", data=OrderSerializer(order).data, status_code=status.HTTP_200_OK)

        orders = Order.objects.filter(customer=request.user)
        return wrap_response(True, "orders_fetched", data=OrderSerializer(orders, many=True).data,status_code=status.HTTP_200_OK)

    def post(self, request):
        serializer = OrderSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return wrap_response(True, "order_created", data=serializer.data, status_code=status.HTTP_201_CREATED)
        return wrap_response(False, "Order creation failed", errors=serializer.errors,status_code=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, order_id):
        order = self.get_object(order_id)
        if not order:
            return wrap_response(False, "order_not_found", message="Order not found", status_code=status.HTTP_404_NOT_FOUND)

        serializer = OrderSerializer(order, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            quantity = serializer.validated_data.get('quantity', order.quantity)
            product = serializer.validated_data.get('product', order.product)
            serializer.save(total_price=product.price * quantity)
            return wrap_response(True, "order_updated", data=serializer.data)
        return wrap_response(False, "order_update_failed", errors=serializer.errors,status_code=status.HTTP_200_OK)

    def delete(self, request, order_id):
        order = self.get_object(order_id)
        if not order:
            return wrap_response(False, "order_not_found", message="Order not found", status_code=status.HTTP_404_NOT_FOUND)
        
        order.delete()
        return wrap_response(True, "order_deleted", message="Order deleted successfully", status_code=status.HTTP_204_NO_CONTENT)
