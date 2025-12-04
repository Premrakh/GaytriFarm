from django.db import models
from uuid import uuid4
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from .manager import UserManager
from django.utils import timezone
class Base(models.Model):
    created = models.DateTimeField(auto_now_add=True, null=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class User(AbstractBaseUser, PermissionsMixin, Base):
    # ---------- USER ROLES ----------
    ADMIN = "admin"
    DISTRIBUTOR = "distributor"
    DELIVERY_STAFF = "delivery_staff"
    CUSTOMER = "customer"
    ROLE_CHOICES = [(ADMIN, "Admin"),(DISTRIBUTOR, "Distributor"),
        (DELIVERY_STAFF, "Delivery Staff"),(CUSTOMER, "Customer"),
    ]

    # ---------- IDENTIFICATION ----------
    user_id = models.AutoField(primary_key=True)
    email = models.EmailField(db_index=True, max_length=100, unique=True,null=True,blank=True)
    mobile = models.CharField(max_length=12, unique=True, null=True, blank=True)
    user_name=models.CharField(max_length=128,unique=True,null=False,blank=False)
    first_name = models.CharField(max_length=128, null=True, blank=True)
    last_name = models.CharField(max_length=128, null=True, blank=True)

    # ---------- ADDRESS ----------
    country = models.CharField(max_length=128, default="India")
    state = models.CharField(max_length=128, default="Gujarat")
    city = models.CharField(max_length=128, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    pin_code = models.IntegerField(null=True, blank=True)

    # ---------- ROLE MANAGEMENT ----------
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, null=True, blank=True)
    role_accepted = models.BooleanField(null=True, blank=True)
    distributor = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True,related_name="distributor_users")
    delivery_staff = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True,related_name="delivery_staff_users")
    rank = models.PositiveIntegerField(default=0)
    # ---------- FINANCIAL ----------
    balance = models.IntegerField(default=0, help_text="Customer balance: payments - delivered orders")
    # ---------- STATUS FLAGS ----------
    is_email_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    # ---------- UTILITY ----------
    fcm_token = models.CharField(max_length=255, null=True, blank=True)   #Firebase Cloud Messaging Token
    reset_password_token = models.CharField(max_length=128, null=True, blank=True)
    
    # ---------- AUTHENTICATION ----------
    USERNAME_FIELD = "user_name"
    REQUIRED_FIELDS = []
    objects = UserManager()

    def __str__(self):
        return self.user_name or ""


class EmailVerificationToken(Base):
    id = models.AutoField(primary_key=True)
    token = models.CharField(max_length=16)
    expiry_date = models.DateTimeField()
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="email_verification_token"
    )

    def __str__(self):
        return str(self.user.email)

class Notification(Base):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255, null=False, blank=False)
    message = models.TextField(null=False, blank=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification to {self.user.user_name}: {self.title}"

class Payment(Base):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payment_transactions")
    amount = models.PositiveIntegerField()
    record_by =  models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,related_name="payment_record_by")

class BankAccount(Base):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="bank_account")
    account_no = models.CharField(max_length=20)
    bank_name = models.CharField(max_length=255)
    holder_name = models.CharField(max_length=255)
    ifsc_code = models.CharField(max_length=11)
    gst_no = models.CharField(max_length=15,null=True,blank=True)
    qr = models.ImageField(upload_to='qr_code/')

    def __str__(self):
        return f"Bank Account for {self.user.user_name}"


class UserBill(Base):
    CUSTOMER_BILL = 'customer_bill'
    DISTRIBUTOR_BILL = 'distributor_bill'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bills')
    total_product = models.PositiveIntegerField(default=0)
    total_amount = models.PositiveIntegerField(default=0)
    pdf_file = models.FileField(upload_to='bills/', null=True, blank=True)
    type = models.CharField(max_length=50, choices=[(CUSTOMER_BILL, 'Customer Bill'), (DISTRIBUTOR_BILL, 'Distributor Bill')], default=CUSTOMER_BILL)
    class Meta:
        ordering = ['-created']

    @property
    def due_date(self):
        # return last month-year like : 2025-10
        return (self.created - timezone.timedelta(days=1)).strftime('%Y-%m')

    def __str__(self):
        return f"Bill for {self.user.user_name}"
