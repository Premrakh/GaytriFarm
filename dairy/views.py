from itertools import product
from django.utils import timezone
from django.shortcuts import render
from gaytri_farm_app.utils import wrap_response, get_object_or_none
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from gaytri_farm_app.custom_permission import (
    IsVerified,  AdminUserPermission, CustomerPermission, DistributorPermission, DeliveryStaffPermission
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
        product_id = request.query_params.get('product_id')
        if pk:
            order = get_object_or_none(Order, id=pk, customer=request.user)
            if not order:
                return wrap_response(False, "order_not_found", message="Order not found")
            return wrap_response(True, "order_fetched", message="Order fetched successfully", data=CustomerOrderSerializer(order).data)
        
        if not product_id:
            return wrap_response(False, "product_id_required", message="product_id query parameter is required")
        now = timezone.now()
        orders = Order.objects.filter(
            customer=request.user,
            product_id=product_id,
            created__year=now.year,
            created__month=now.month
        ).order_by('created').values('product', 'date', 'status')
        # serializer = CustomerOrderSerializer(orders, many=True)
        return wrap_response(True, "orders_fetched", message="Orders fetched successfully", data=orders)

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
        
        # Base query based on user role
        if user.role == User.DELIVERY_STAFF:
            orders = Order.objects.filter(delivery_staff=user)
        elif user.role == User.DISTRIBUTOR:
            orders = Order.objects.filter(customer__distributor=user)
        elif user.is_superuser:
            orders = Order.objects.all()
        else:
            return wrap_response(False, "permission_denied", message="Permnission denied")
        
        # Apply filters from query parameters
        # Date filter: today/tomorrow
        day_filter = request.query_params.get('day')
        if day_filter:
            today = timezone.now().date()
            if day_filter.lower() == 'today':
                orders = orders.filter(date=today)
            elif day_filter.lower() == 'tomorrow':
                tomorrow = today + timezone.timedelta(days=1)
                orders = orders.filter(date=tomorrow)
        
        # User filter (customer filter)
        user_id = request.query_params.get('user_id')
        if user_id:
            orders = orders.filter(customer__user_id=user_id)
        
        # Product filter
        product_id = request.query_params.get('product_id')
        if product_id:
            orders = orders.filter(product__id=product_id)
        
        # Optimize: fetch related objects in single query (both User FKs + Product FK)
        orders = orders.select_related('customer', 'delivery_staff', 'product').order_by('created')
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


class CustomerMonthlyBillView(APIView):
    permission_classes = [IsAuthenticated, IsVerified]

    def post(self, request):
        user = request.user
        serializer = CustomerBillDetailSerializer(data=request.data)
        if serializer.is_valid():
            month = serializer.validated_data['month']
            year = serializer.validated_data['year']
            user_id = serializer.validated_data.get('customer_id')
            if user.role == User.CUSTOMER:
                customer = user
            elif user.is_superuser or user.role == User.DISTRIBUTOR:
                customer = User.objects.filter(user_id=user_id, role=User.CUSTOMER).first()
            else:
                return wrap_response(False,"permission_denied",message="Permission denied")
            if not customer:
                return wrap_response(False,"customer_not_found",message="Customer not found")

            orders = Order.objects.filter(
                customer=customer,
                status=Order.DELIVERED,
                date__month=month,
                date__year=year
            ).select_related('product').values(
                'product__name',
            ).annotate(
                total_quantity=models.Sum('quantity'),
                total_amount=models.Sum('total_price')
            )
            # Skip if no orders
            if not orders:
                return wrap_response(False,"no_orders",message=f'No delivered orders found for {month}/{year}')
            
            # Calculate totals
            grand_total = sum(order['total_amount'] for order in orders)
            total_items = sum(order['total_quantity'] for order in orders)
            
            # Build product-wise breakdown
            product_breakdown = [
                {
                    "product_name": order['product__name'],
                    "quantity": order['total_quantity'],
                    "total_amount": order['total_amount']
                }
                for order in orders
            ]
            
            # Create bill data structure
            bill_data = {
                "customer_id": str(customer.user_id),
                "customer_name": customer.user_name,
                "total_items": total_items,
                "total_amount": grand_total,
                "product_breakdown": product_breakdown,
            }
            return wrap_response(True, "bill_retrieved", data=bill_data, message="Monthly bill retrieved successfully.")
            
        return wrap_response(False, "invalid_data", message="Invalid data", errors=serializer.errors)
    

class MonthlyRevenueView(APIView):
    permission_classes = [IsAuthenticated, IsVerified, DistributorPermission]

    def get(self, request):
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        if not month or not year:
            return wrap_response(False, "month_year_required", message="month and year query parameters are required")
        try:
            month = int(month)
            year = int(year)
        except ValueError:
            return wrap_response(False, "invalid_month_year", message="month and year must be integers")
        
        total_revenue = Order.objects.filter(
            customer__distributor=request.user,
            status=Order.DELIVERED,
            date__month=month,
            date__year=year
        ).aggregate(total_revenue=models.Sum('total_price'))['total_revenue'] or 0
        
        return wrap_response(True, "monthly_revenue", data={"month": month, "year": year, "total_revenue": total_revenue}, message="Monthly revenue fetched successfully.")