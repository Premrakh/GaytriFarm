from rest_framework import serializers
from .models import User, Payment, QrCode
import re

class UserRegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    user_name = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)
    class Meta:
        model = User
        fields = ['email', 'mobile', 'user_name', 'first_name', 'last_name', 'country', 'state', 'city', 'address', 'pin_code', 'password', 'confirm_password']
    
    def validate_password(self, value):
        pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
        if not re.match(pattern, value):
            raise serializers.ValidationError("Password must contain at least 8 characters, one uppercase letter, one lowercase letter, one digit, and one special character.")
        return value
    
    
class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField(write_only=True, max_length=16)


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)


class UserRoleSerializer(serializers.Serializer):
    role = serializers.CharField(required=True)
    distributor_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs):
        role = attrs.get('role')
        distributor_id = attrs.get('distributor_id')
        valid_roles = [User.DISTRIBUTOR, User.DELIVERY_STAFF, User.CUSTOMER]
        if role not in valid_roles:
            raise serializers.ValidationError("Invalid role. Must be one of: {}".format(", ".join(valid_roles)))
        
        if not role == User.DISTRIBUTOR:
            if not distributor_id:
                raise serializers.ValidationError("Distributor must be provided when role is Customer or Delivery Staff.")
        if role == User.DISTRIBUTOR and distributor_id:
            raise serializers.ValidationError("Distributor should not be provided when role is Distributor.")

        return super().validate(attrs)

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)
    token = serializers.CharField(required=True)

    def validate_password(self, value):
        pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                "Password must contain at least 8 characters, one uppercase letter, one lowercase letter, one digit, and one special character."
            )
        return value
    
    def validate_confirm_password(self, value):
        password = self.initial_data.get("password")
        if password != value:
            raise serializers.ValidationError("password and confirm_password fields didn't match.")
        return value

class AccountSerializer(serializers.ModelSerializer):
    distributor = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = User
        exclude = ['password' , 'reset_password_token', 'fcm_token' , 'groups', 'user_permissions']

class UpdateAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['user_name', 'mobile','first_name','last_name',
                 'country','state','city','address','pin_code']

class EnrollUsersSerializer(serializers.ModelSerializer):
    delivery_staff_name = serializers.CharField(source='delivery_staff.user_name', read_only=True)
    is_next_order = serializers.BooleanField(read_only=True)
    class Meta:
        model = User
        # exclude = ['password' , 'reset_password_token', 'fcm_token' , 'groups', 'user_permissions']
        fields = ['user_id','user_name','email','mobile', 'delivery_staff','delivery_staff_name' ,'first_name','last_name',
                 'country','state','city','address','pin_code','is_next_order','is_active']

class UserApprovalSerializer(serializers.Serializer):
    user_id  = serializers.UUIDField()
    action = serializers.BooleanField()

class CustomerApprovalSerializer(UserApprovalSerializer):
    delivery_staff_id  = serializers.UUIDField()
    

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value
    
    def validate_password(self, value):
        pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                "Password must contain at least 8 characters, one uppercase letter, one lowercase letter, one digit, and one special character."
            )
        return value


class AddCustomerSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    user_name = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)
    class Meta:
        model = User
        fields = ['email', 'user_name', 'password', 'confirm_password','delivery_staff','first_name','last_name',
                 'country','state','city','address','pin_code','mobile']

class CustomerRankSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True)
    rank = serializers.IntegerField(required=True, min_value=1)

class RouteSetupSerializer(serializers.Serializer):
    delivery_staff_id = serializers.IntegerField(required=False)
    customers = CustomerRankSerializer(many=True)

    # validate delivery staff id if login user is distributor then requiered otherwise not 
    def validate(self, attrs):
        delivery_staff_id = attrs.get('delivery_staff_id')
        user = self.context['request'].user
        if user.role != User.DELIVERY_STAFF:
            if not delivery_staff_id:
                raise serializers.ValidationError("Delivery staff id is required.")
        return super().validate(attrs)

class PaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Payment
        fields = ['id','user', 'amount','created']

class QrCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = QrCode
        fields = ["id", "qr"]
        read_only_fields = ["id"]