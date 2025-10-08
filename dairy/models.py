from uuid import uuid4
from django.db import models
from user.models import User , Base
# Create your models here.

class Product(Base):
    name = models.CharField(max_length=255, null=False, blank=False)
    description = models.TextField(null=True, blank=True)
    price = models.PositiveIntegerField()   
    def __str__(self):
        return self.name
    
class Order(Base):
    order_id = models.UUIDField(primary_key=True, default=uuid4, editable=False, unique=True)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    delivery_staff = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deliveries')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.PositiveIntegerField()
    order_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order_id}"