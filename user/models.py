from django.db import models
from uuid import uuid4
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from .manager import UserManager

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
    user_id = models.UUIDField(primary_key=True, default=uuid4, editable=False, unique=True)
    email = models.EmailField(db_index=True, max_length=100, unique=True,null=True,blank=True)
    user_name=models.CharField(max_length=128,unique=True,null=False,blank=False)


    # ---------- ROLE MANAGEMENT ----------
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, null=True, blank=True)
    role_accepted = models.BooleanField(null=True, blank=True)
    distributor = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True,related_name="distributor_users")
    delivery_staff = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True,related_name="delivery_staff_users")

    # ---------- STATUS FLAGS ----------
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_registered = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)

    # ---------- NOTIFICATION ----------
    fcm_token = models.CharField(max_length=255, null=True, blank=True)   #Firebase Cloud Messaging Token
    allow_notification=models.BooleanField(default=True)

    # ---------- UTILITY ----------
    reset_password_token = models.CharField(max_length=128, null=True, blank=True)
    
    # ---------- AUTHENTICATION ----------
    USERNAME_FIELD = "user_name"
    REQUIRED_FIELDS = []
    objects = UserManager()

    def save(self, *args, **kwargs):
        if self.country:
            self.country = self.country.title()
        if self.state:
            self.state = self.state.title()
        if self.city:
            self.city = self.city.title()
        super().save(*args, **kwargs)


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

class UserProfile(Base):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    first_name = models.CharField(max_length=128, null=True, blank=True)
    last_name = models.CharField(max_length=128, null=True, blank=True)
    country = models.CharField(max_length=128, default="India")
    state = models.CharField(max_length=128, default="Gujarat")
    city = models.CharField(max_length=128, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    pin_code = models.IntegerField(null=True,blank=True)