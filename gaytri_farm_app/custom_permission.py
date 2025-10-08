from rest_framework.permissions import BasePermission
from rest_framework.exceptions import APIException,PermissionDenied
from gaytri_farm_app.utils import wrap_response
from django.utils import timezone
from user.models import User

class IsVerified(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_email_verified:
            return True
        else:
            raise PermissionDenied(detail={
                "success": False,
                "code": "email_not_verified",
                "data":{
                    "is_email_verified":False
                },
                "message": "Email not verified."
            })


class IsRegistered(BasePermission):
    def has_permission(self, request, view):
        if  request.user.role_accepted:
            return True
        raise PermissionDenied(detail={
            "success": False,
            "code": "user_not_registered",
            "data":{
                "role_accepted":False
            },
            "message": "User not registered."
        })
    

class AdminUserPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_superuser:
                return True
        raise PermissionDenied(detail={
            "success": False,
            "code": "user_not_admin",
            "data":{
                "is_superuser":False
            },
            "message": "User is not an admin."
        })

class DistributorPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.role == request.user.DISTRIBUTOR and request.user.role_accepted:
                return True
        raise PermissionDenied(detail={
            "success": False,
            "code": "user_not_distributor",
            "data":{
                "role":request.user.role,
                "role_accepted":request.user.role_accepted
            },
            "message": "User is not a distributor."
        })

class DeliveryStaffPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.role == request.user.DELIVERY_STAFF and request.user.role_accepted:
                return True
        raise PermissionDenied(detail={
            "success": False,
            "code": "user_not_delivery_staff",
            "data":{
                "role":request.user.role,
                "role_accepted":request.user.role_accepted
            },
            "message": "User is not a delivery staff."
        })

class CustomerPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.role == request.user.CUSTOMER and request.user.role_accepted:
                return True
        raise PermissionDenied(detail={
            "success": False,
            "code": "user_not_customer",
            "data":{
                "role":request.user.role,
                "role_accepted":request.user.role_accepted
            },
            "message": "User is not a customer."
        })


class AdminOrDistributorPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.role == User.DISTRIBUTOR and request.user.role_accepted:
                return True
        if request.user.is_superuser:
                return True
        raise PermissionDenied(detail={
            "success": False,
            "code": "user_not_distributor_or_admin",
            "data":{
                "role":request.user.role,
            },
            "message": "User is neither a distributor nor an admin."
        })