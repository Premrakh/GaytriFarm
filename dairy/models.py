from random import choices
from uuid import uuid4
from django.db import models
from user.models import User , Base
from django.utils import timezone
# Create your models here.

class Product(Base):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    price = models.PositiveIntegerField()  
    distributor_price = models.PositiveIntegerField(null=True, blank=True)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    is_primary = models.BooleanField(default=False)
    def __str__(self):
        return self.name
    
class Order(Base):
    PENDING = 'pending'
    DELIVERED = 'delivered'
    CANCELED = 'cancel'

    ORDER_CHOICES = [
        (PENDING, 'Pending'),
        (DELIVERED, 'Delivered'),
        (CANCELED, 'Cancel'),
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    delivery_staff = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deliveries')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.PositiveIntegerField()
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=50, choices=ORDER_CHOICES, default=PENDING)

    def __str__(self):
        return f"{self.id}"

class UserBill(Base):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bills')
    total_product = models.PositiveIntegerField(default=0)
    total_amount = models.PositiveIntegerField(default=0)
    pdf_file = models.FileField(upload_to='bills/', null=True, blank=True)
    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f"Bill for {self.user.user_name}"

class DistributorOrder(Base):
    distributor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='distributor_orders')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    total_price = models.PositiveIntegerField()
    
    def __str__(self):
        return f"Order for {self.distributor.user_name}"