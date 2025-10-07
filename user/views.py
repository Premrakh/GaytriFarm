from email.mime import message
import token
from rest_framework.views import APIView
from rest_framework import status
import random, string
from django.utils import timezone
from .models import User, EmailVerificationToken
from .serializers import (EnrollUsersSerializer, ResetPasswordSerializer, UserApprovalSerializer, UserRegisterSerializer, EmailVerificationSerializer, UserLoginSerializer,
        UserProfileSerializer, UserRoleSerializer, AccountSerializer, UserApprovalSerializer, CustomerApprovalSerializer
                          )
from gaytri_farm_app.utils import wrap_response
from .service import generate_token, send_forgot_password_email, send_verification_email, unzip_token
from rest_framework.permissions import IsAuthenticated
from gaytri_farm_app.custom_permission import (IsVerified, IsRegistered, AdminUserPermission, DistributorPermission,
         DeliveryStaffPermission, CustomerPermission
)
from rest_framework_simplejwt.tokens import RefreshToken

# Create your views here.


class UserRegistrationView(APIView):
    authentication_classes=[]
    permission_classes = []
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return wrap_response(False, "invalid_data", errors=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        email = serializer.validated_data.get('email')
        user_name = serializer.validated_data.get('user_name')
        password = serializer.validated_data.get('password')
        confirm_password = serializer.validated_data.get('confirm_password')
        if password != confirm_password:
            return wrap_response(False, "password_mismatch", message="Password and Confirm Password do not match.", status_code=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(email=email, user_name=user_name).exists():
            return wrap_response(False, "user_exists", 
                                    message="A user with this email and username already exists.", 
                                    status_code=status.HTTP_400_BAD_REQUEST
                                    )
        user = User.objects.create_user(email=email, user_name=user_name, password=password)
        user.save()
        # Generate a verification token 6 number code
        token = str(random.randint(100000, 999999))
        EmailVerificationToken.objects.create(
            user=user,
            token=token,
            expiry_date=timezone.now() + timezone.timedelta(minutes=5),
        )
        res = send_verification_email(email, token)
        if not res:
            User.objects.filter(user_id=user.user_id).delete()
            return wrap_response(False, 
                                    code="email_send_failed", 
                                    message="Failed to send verification email. Please try again later.",
                                    status_code=status.HTTP_400_BAD_REQUEST
                        )
        refresh_token = RefreshToken.for_user(user)
        data = {
            "user_id": user.user_id,
            "email": user.email,
            "refresh": str(refresh_token),
            "access": str(refresh_token.access_token),
        }
        return wrap_response(True, "user_registered", data=data, message="User registered successfully.")

class SendEmailTokenView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        user = request.user
        if user.is_email_verified:
            return wrap_response(
                success=False,
                code="email_already_verified",
                message="Email already verified."
            )
        token = str(random.randint(100000, 999999))
        verify_token = EmailVerificationToken.objects.create(
                user=user,
                token=token,
                expiry_date=timezone.now() + timezone.timedelta(minutes=5),
            )
        res = send_verification_email(user.email, token)
        if not res:
            verify_token.delete()
            return wrap_response(False, code="email_send_failed", message="Failed to send verification email. Please try again later.")
        return wrap_response(True, "token_sent", message="Verification token sent to email successfully.")

class EmailVerificationView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = EmailVerificationSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            try:
                user=User.objects.get(email=user.email)
            except User.DoesNotExist:
                return wrap_response(success=False, code="user_not_exist", message="User with this email does not exist.")
            if user.is_email_verified:
                return wrap_response(success=False, code="email_already_verified", message="Email already verified.")
            try:
                verification_token=EmailVerificationToken.objects.get(user=user)
            except EmailVerificationToken.DoesNotExist:
                return wrap_response(success=False, code="token_not_exist", message="Verification token does not exist for the provided email.")
            if verification_token.token != serializer.validated_data["token"]:
                return wrap_response(success=False, code="invalid_token", message="Invalid verification code.")
            if verification_token.expiry_date < timezone.now():
                verification_token.delete()
                return wrap_response(success=False,code="token_expired",message="The verification code has expired and should be verified within 5 minutes of sending.")
            user.is_active = True
            user.is_email_verified = True
            user.save()
            verification_token.delete()
            data = {
                "user_id": user.user_id,
                "is_email_verified": user.is_email_verified,
                "role_accepted": user.role_accepted,
                "role": user.role,
                "is_superuser": user.is_superuser,
            }
            return wrap_response(
                success=True,
                code="email_verified",
                message="Email verified successfully.",
                status_code=status.HTTP_200_OK,
            )

class UserLoginView(APIView):
    authentication_classes = []
    permission_classes = []
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return wrap_response(
                success=False,
                code="login_failed",
                message="Login failed. Please check your credentials.",
                errors=serializer.errors,
            )
        user_name = serializer.validated_data.get("user_name")
        email = serializer.validated_data.get("email")
        password = serializer.validated_data.get("password")

        try:
            if user_name:
                user = User.objects.get(user_name=user_name)
            else:
                user = User.objects.get(email=email)
            if user.check_password(password):
                refresh = RefreshToken.for_user(user)
                data = {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "user_id": user.user_id,
                    "email_verified": user.is_email_verified,
                    "role_accepted": user.role_accepted,
                    "role": user.role,
                    "is_superuser": user.is_superuser,
                }
                return wrap_response(
                    success=True,
                    code="login_successful",
                    message="User logged in successfully.",
                    data=data
                )
            else:
                return wrap_response(success=False, code="invalid_credentials", message="Invalid credentials. Please try again.")
        except User.DoesNotExist:
            return wrap_response(
                success=False,
                code="user_not_found",
                message="User with the provided credentials does not exist.",
            )

class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return wrap_response(False, "token_missing", message="Refresh token is required.")
            token = RefreshToken(refresh_token)
            if token['user_id'] != str(request.user.user_id):
                return wrap_response(False, "invalid_token", message="Invalid token for the user.")
            token.blacklist()
            return wrap_response(True, "logout_successful", message="User logged out successfully.")
        except Exception as e:
            return wrap_response(False, "logout_failed", message="Logout failed. Please try again.", errors=str(e))

class UserProfile(APIView):
    permission_classes = [IsAuthenticated, IsVerified]
    def get(self, request):
        if not hasattr(request.user, 'profile'):
            return wrap_response(False, "profile_not_found", message="User profile not found.")
        serializer = UserProfileSerializer(request.user.profile)
        return wrap_response(True, "profile_retrieved", data=serializer.data, message="User profile retrieved successfully.")

    def post(self, request):
        user = request.user
        serializer = UserProfileSerializer(data=request.data)
        if not serializer.is_valid():
            return wrap_response(False, "invalid_data", message="Invalid data", errors=serializer.errors)
        serializer.save(user=user)
        return wrap_response(True, "profile_added", data=serializer.data, message="User profile added successfully.")

    def patch(self, request):
        if not hasattr(request.user, 'profile'):
            return wrap_response(False, "profile_not_found", message="User profile not found.")
        serializer = UserProfileSerializer(request.user.profile, data=request.data, partial=True)
        if not serializer.is_valid():
            return wrap_response(False, "invalid_data", message="Invalid data", errors=serializer.errors)
        serializer.save()
        return wrap_response(True, "profile_updated", data=serializer.data, message="User profile updated successfully.")

class UserRoleView(APIView):
    '''Select role for user like distributor, delivery staff, customer'''
    permission_classes = [IsAuthenticated, IsVerified]
    def post(self, request):
        user = request.user
        serializer = UserRoleSerializer(data=request.data)
        if not serializer.is_valid():
            return wrap_response(False, "invalid_data", message="Invalid data", errors=serializer.errors)
        role = serializer.validated_data.get('role')
        distributor_id = serializer.validated_data.get('distributor_id')
        try:
            user.role = role
            if distributor_id:  
                distributor = User.objects.get(user_id=distributor_id)
                user.distributor = distributor
            user.save()
            return wrap_response(True, "role_updated", message="User role updated successfully.")
        except User.DoesNotExist:
            return wrap_response(False, "distributor_not_found", message="Distributor not found.", status_code=status.HTTP_404_NOT_FOUND)
    
    
class AccountView(APIView):
    permission_classes = [IsAuthenticated, IsVerified]
    def get(self,request):
        serializer = AccountSerializer(request.user)
        return wrap_response(True,code='account_retrieved', data=serializer.data)


class UpdateFCMTokenView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        fcm_token = request.data.get("fcm_token")
        if not fcm_token:
            return wrap_response(False, "missing_token", message="FCM token is required.")
        user = request.user
        user.fcm_token = fcm_token
        user.save()
        return wrap_response(True, "token_updated", message="FCM token updated successfully.")

class ForgotPasswordView(APIView):
    permission_classes=[]
    authentication_classes=[]
    def post(self, request, *args, **kwargs):
        email = request.data.get('email', None)
        if not email:
            return wrap_response(
                success=False,
                code="email_required",
                message="Email is required."
            )
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return wrap_response(
                success=False,
                code="user_not_found",
                message="User with this email does not exist."

            )
        
        reset_token = generate_token(user.user_id)
        res = send_forgot_password_email(
            user.email, reset_token
        )
        if not res:
            return wrap_response(
                success=False,
                code="failed_to_send_verification_email",
                message="Failed to send verification email."
            )
        user.reset_password_token= reset_token
        user.save()
        return wrap_response(
            success=True,
            code="reset_password_mail_sent",
            message="Reset password mail sent successfully.",
        )

class ResetPasswordView(APIView):
    permission_classes=[]
    authentication_classes=[]
    def post(self, request, *args, **kwargs):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return wrap_response(False, "invalid_data",message="Invalid data", errors=serializer.errors)
        auth_token = serializer.validated_data['token']
        user_id, error =unzip_token(auth_token)
        if user_id is None:
            if error=="invalid_token":
                message="Invalid token"
            else:
                message="Expired token. Please generate new reset password url."
            return wrap_response(
                success=False,
                code=error,
                message=message,
            )
        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return wrap_response(
                success=False,
                code="user_not_found",
                message="User not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        if user.reset_password_token!=auth_token:
            return wrap_response(
                success=False,
                code="token_already_used",
                message="This URl already used for resetting password.",
            )
        user.set_password(serializer.validated_data['password'])
        user.reset_password_token=None
        user.save()
        return wrap_response(
            success=True,
            code="password_reset_successful",
            message="Password reset successful."
        )
        
class RoleWiseUsersView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, role):
        valid_roles = User.ROLE_CHOICES
        valid_roles = [r[0] for r in valid_roles]
        if role not in valid_roles:
            return wrap_response(False, "invalid_role", message=f"Role must be one of the following: {', '.join(valid_roles)}")
        users = User.objects.filter(role=role).values("user_id","user_name")
        return wrap_response(True, "users_retrieved", data=users, message=f"Users with role {role} retrieved successfully.")

class CustomersView(APIView):
    ''' This view is for distributor to see their customers'''
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated(), IsVerified(), DistributorPermission() | AdminUserPermission()]
        else:
            return [IsAuthenticated(), IsVerified(), DistributorPermission()]

    def get(self, request):
        user = request.user
        role_accepted = request.query_params.get('role_accepted')
        if user.role == User.DISTRIBUTOR:
            if role_accepted in [True, False]:
                customers = User.objects.filter(role=User.CUSTOMER, distributor=request.user, role_accepted=role_accepted).order_by('-created')
            else:
                return wrap_response(False, "invalid_role_accepted", message="role_accepted must be true or false.")
        else:
            customers = User.objects.filter(role=User.CUSTOMER, role_accepted=True).order_by('-created')

        serializer = EnrollUsersSerializer(customers, many=True)
        return wrap_response(True, "customers_list", data=serializer.data, message="Customers fetched successfully.")
    
    def post(self, request):
        serializer = CustomerApprovalSerializer(data=request.data)
        if serializer.is_valid():
            user_id = serializer.validated_data.get('user_id')
            delivery_staff_id = serializer.validated_data.get('delivery_staff_id')
            action = serializer.validated_data.get('action')
            if action==False:
                users = User.objects.filter(user_id=user_id, role=User.CUSTOMER).update(role_accepted=action)
            else:
                if not User.objects.filter(user_id=delivery_staff_id, role=User.DELIVERY_STAFF).exists():
                    return wrap_response(False, "invalid_delivery_staff", message="Invalid delivery staff ID.")

                users = User.objects.filter(user_id=user_id, role=User.CUSTOMER).update(role_accepted=action, delivery_staff_id=delivery_staff_id)
                if users == 0:
                    return wrap_response(False, "no_users_updated", message="No users were updated. Please check the provided user IDs.")

            return wrap_response(True, "users_updated", message="Customer approval status updated successfully.")    
        return wrap_response(False, "invalid_data", message="Invalid data", errors=serializer.errors)
    
class DeliveryStaffView(APIView):
    ''' This view is for Admin/distributor to see their delivery staff'''
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated(), IsVerified(), DistributorPermission() | AdminUserPermission()]
        else:
            return [IsAuthenticated(), IsVerified(), DistributorPermission()]
        
    def get(self, request):
        user = request.user
        role_accepted = request.query_params.get('role_accepted')
        if user.role == User.DISTRIBUTOR:
            if role_accepted in [True, False]:
                customers = User.objects.filter(role=User.DELIVERY_STAFF, distributor=user, role_accepted=role_accepted).order_by('-created')
            else:
                return wrap_response(False, "invalid_role_accepted", message="role_accepted must be true or false.")
        else:
            customers = User.objects.filter(role=User.DELIVERY_STAFF, role_accepted=True).order_by('-created')
        serializer = EnrollUsersSerializer(customers, many=True)
        return wrap_response(True, "customers_list", data=serializer.data, message="Customers fetched successfully.")
    
    def post(self, request):
        serializer = UserApprovalSerializer(data=request.data)
        if serializer.is_valid():
            user_id = serializer.validated_data.get('user_id')
            action = serializer.validated_data.get('action')
            users = User.objects.filter(user_id=user_id, role=User.DELIVERY_STAFF).update(role_accepted=action)
            if users == 0:
                return wrap_response(False, "no_users_updated", message="No users were updated. Please check the provided user IDs.")

            return wrap_response(True, "users_updated", message="Delivery staff approval status updated successfully.")    
        return wrap_response(False, "invalid_data", message="Invalid data", errors=serializer.errors)

class DistributorView(APIView):
    ''' This view is for admin to approve/reject distributors'''
    permission_classes = [IsAuthenticated, IsVerified, AdminUserPermission]
    def get(self, request):
        role_accepted = request.query_params.get('role_accepted')
        if role_accepted in [True, False]:
            users = User.objects.filter(role=User.DISTRIBUTOR, role_accepted=role_accepted).order_by('-created')
            return wrap_response(True, "distributors_list", data=EnrollUsersSerializer(users, many=True).data, message="Distributors fetched successfully.")
        return wrap_response(False, "invalid_role_accepted", message="role_accepted must be true or false.")

    def post(self, request):
        serializer = UserApprovalSerializer(data=request.data)
        if serializer.is_valid():
            user_id = serializer.validated_data.get('user_id')
            action = serializer.validated_data.get('action')
            users = User.objects.filter(user_id=user_id, role=User.DISTRIBUTOR).update(role_accepted=action)
            if users == 0:
                return wrap_response(False, "no_users_updated", message="No users were updated. Please check the provided user IDs.")

            return wrap_response(True, "users_updated", message="Distributor approval status updated successfully.")    
        return wrap_response(False, "invalid_data", message="Invalid data", errors=serializer.errors)
