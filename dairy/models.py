from random import choices
from uuid import uuid4
from django.db import models
from user.models import User , Base
# Create your models here.

class Product(Base):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    price = models.PositiveIntegerField()   
    def __str__(self):
        return self.name
    
class Order(Base):
    PENDING = 'pending'
    DELIVERED = 'delivered'
    CANCELED = 'canceled'

    ORDER_CHOICES = [
        (PENDING, 'Pending'),
        (DELIVERED, 'Delivered'),
        (CANCELED, 'Canceled'),
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    delivery_staff = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deliveries')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=ORDER_CHOICES, default=PENDING)

    def __str__(self):
        return f"{self.id}"