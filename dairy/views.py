from django.shortcuts import render
from gaytri_farm_app.utils import wrap_response
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from gaytri_farm_app.custom_permission import (
    IsVerified,  AdminUserPermission, CustomerPermission, DistributorPermission, DeliveryStaffPermission
)
from .models import *
from .serializers import *

def get_object_or_none(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        return None

# Product Views
class ProductDetailAPIView(APIView):
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated(), IsVerified()]
        else:
            return [IsAuthenticated(), IsVerified(), AdminUserPermission()]
        
    def get(self, request, pk=None):
        if pk:
            product = get_object_or_none(Product, pk=pk)
            if not product:
                return wrap_response(
                    success=False,
                    code="PRODUCT_NOT_FOUND",
                    message="Product not found"
                )
            serializer = ProductSerializer(product)
            return wrap_response(True, "Product fetched successfully", data=serializer.data)

        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return wrap_response(True, "Products fetched successfully", data=serializer.data)

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return wrap_response(True, "product_created", data=serializer.data, message="Product created successfully")
        return wrap_response(False, "invalid_data", message="Invalid data", errors=serializer.errors)

    def patch(self, request, pk):
        product = get_object_or_none(Product, pk=pk)
        if not product:
            return wrap_response(
                False, "PRODUCT_NOT_FOUND", message="Product not found",
            )
        serializer = ProductSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return wrap_response(True, "product_updated", message="Product updated successfully", data=serializer.data)
        return wrap_response(False, "invalid_data", message="Invalid data", errors=serializer.errors)

    def delete(self, request, pk):
        product = get_object_or_none(Product, pk=pk)
        if not product:
            return wrap_response(
                False, "PRODUCT_NOT_FOUND", message="Product not found",
            )
        product.delete()
        return wrap_response(True, "product_deleted", message="Product deleted successfully")


#  Customer Order Views
class CustomerOrderView(APIView):
    ''' This view is for Customer to manage their orders'''
    permission_classes = [IsAuthenticated, IsVerified, CustomerPermission]
    
    def get(self, request, pk=None):
        if pk:
            order = get_object_or_none(Order, id=pk, customer=request.user)
            if not order:
                return wrap_response(False, "order_not_found", message="Order not found")
            return wrap_response(True, "order_fetched", message="Order fetched successfully", data=CustomerOrderSerializer(order).data)

        orders = Order.objects.filter(customer=request.user).order_by('-created')
        serializer = CustomerOrderSerializer(orders, many=True)
        return wrap_response(True, "orders_fetched", message="Orders fetched successfully", data=serializer.data)

    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        if serializer.is_valid():
            product = serializer.validated_data['product']
            quantity = serializer.validated_data['quantity']

            Order.objects.create(
                customer=request.user,
                delivery_staff=request.user.delivery_staff,
                product=product,
                quantity=quantity,
                total_price=product.price * quantity
            )
            return wrap_response(True, "order_created", message="Order created successfully", data=serializer.data)
        return wrap_response(False, "invalid_data", message="Invalid data", errors=serializer.errors)

    def put(self, request, pk):
        order = get_object_or_none(Order, id=pk, customer=request.user)
        if not order:
            return wrap_response(False, "order_not_found", message="Order not found")

        serializer = OrderCreateSerializer(order, data=request.data)
        if serializer.is_valid():
            product = serializer.validated_data['product']
            quantity = serializer.validated_data['quantity']
            serializer.save(total_price=product.price * quantity)
            return wrap_response(True, "order_updated", message="Order updated successfully", data=serializer.data)
        return wrap_response(False, "order_update_failed", message="Order update failed", errors=serializer.errors)

    def delete(self, request, pk):
        order = get_object_or_none(Order, id=pk, customer=request.user)
        if order:
            order.delete()
            return wrap_response(True, "order_deleted", message="Order deleted successfully")
        return wrap_response(False, "order_not_found", message="Order not found")



class ManageOrderAPI(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated(), IsVerified()]
        else:
            return [IsAuthenticated(), IsVerified(), DeliveryStaffPermission()]

    def get(self, request):
        user = request.user
        if user.role == User.DELIVERY_STAFF:
            orders = Order.objects.filter(delivery_staff=user).order_by('created')
        elif user.role == User.DISTRIBUTOR:
            orders = Order.objects.filter(customer__distributor=user).order_by('created')
        elif user.is_superuser:
            orders = Order.objects.all().order_by('created')
        else:
            return wrap_response(False, "permission_denied", message="Permnission denied")
        serializer = ManagerOrderSerializer(orders, many=True)
        return wrap_response(True, "orders_list", data=serializer.data, message="Orders fetched successfully.")

    def patch(self, request, pk):
        user = request.user
        order = get_object_or_none(Order, pk=pk, delivery_staff=user)
        if not order:
            return wrap_response(False, "order_not_found", message="Order not found")
        status_value = request.data.get("status")
        if status_value not in [Order.DELIVERED, Order.CANCELED]:
            return wrap_response(False, "invalid_data", message=f"status must be either {Order.DELIVERED} or {Order.CANCELED}.")
        order.status = status_value
        order.save()
        serializer = ManagerOrderSerializer(order)
        return wrap_response(True, "order_updated", data=serializer.data, message="Order status updated successfully.")