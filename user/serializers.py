from rest_framework import serializers
from .models import User, UserProfile
import re

class UserRegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    user_name = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)
    class Meta:
        model = User
        fields = ['email', 'user_name', 'password', 'confirm_password']
    
    def validate_password(self, value):
        pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
        if not re.match(pattern, value):
            raise serializers.ValidationError("Password must contain at least 8 characters, one uppercase letter, one lowercase letter, one digit, and one special character.")
        return value
    
    
class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField(write_only=True, max_length=16)


class UserLoginSerializer(serializers.Serializer):
    user_name = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    password = serializers.CharField(required=True)

    def validate(self, data):
        user_name = data.get('user_name', None)
        email = data.get('email', None)

        if not user_name and not email:
            raise serializers.ValidationError("Either user_name or email must be provided.")

        return data

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        exclude = ['user']

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
    password = serializers.CharField(required=True,allow_null=False,allow_blank=False)
    confirm_password = serializers.CharField(required=True,allow_null=False,allow_blank=False)
    token = serializers.CharField(required=True,allow_null=False,allow_blank=False)

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
    class Meta:
        model = User
        exclude = ['password' , 'reset_password_token', 'fcm_token' , 'groups', 'user_permissions']

class EnrollUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['user_id', 'user_name','email','role_accepted']

class UserApprovalSerializer(serializers.Serializer):
    user_id  = serializers.UUIDField()
    action = serializers.BooleanField()

class CustomerApprovalSerializer(UserApprovalSerializer):
    delivery_staff_id  = serializers.UUIDField()
    


from django.contrib.auth import get_user_model

User = get_user_model()

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

  