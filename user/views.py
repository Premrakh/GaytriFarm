from email.mime import message
from rest_framework.views import APIView
from rest_framework import status
import random, string
from django.utils import timezone
from .models import User, EmailVerificationToken, Payment
from dairy.models import Order
from .serializers import (EnrollUsersSerializer, ResetPasswordSerializer, UpdateAccountSerializer, UserApprovalSerializer, UserRegisterSerializer, 
        EmailVerificationSerializer, UserLoginSerializer, UserRoleSerializer, AccountSerializer, UserApprovalSerializer,
        CustomerApprovalSerializer,ChangePasswordSerializer, AddCustomerSerializer, RouteSetupSerializer,PaymentSerializer)
from gaytri_farm_app.utils import wrap_response, get_object_or_none
from .service import send_forgot_password_email, send_verification_email
from rest_framework.permissions import IsAuthenticated
from gaytri_farm_app.custom_permission import (IsVerified, IsRegistered, AdminUserPermission, DistributorPermission, AdminOrDistributorPermission, CustomerPermission
)
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import OuterRef, Exists, Q, Sum
from django.db import transaction
from dateutil.relativedelta import relativedelta
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
        user = User.objects.create_user(
                email=email,
                user_name=user_name,
                password=password,
                mobile=serializer.validated_data.get('mobile'),
                first_name=serializer.validated_data.get('first_name'),
                last_name=serializer.validated_data.get('last_name'),
                country=serializer.validated_data.get('country'),
                state=serializer.validated_data.get('state'),
                city=serializer.validated_data.get('city'),
                address=serializer.validated_data.get('address'),
                pin_code=serializer.validated_data.get('pin_code')
            )
        # user.save()
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
        EmailVerificationToken.objects.filter(user=user).delete()

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
            if user.is_email_verified:
                return wrap_response(success=False, code="email_already_verified", message="Email already verified.")
            verification_token = get_object_or_none(EmailVerificationToken, user=user)
            if not verification_token:
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
                message="Email verified successfully."
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
        email = serializer.validated_data.get("email")
        password = serializer.validated_data.get("password")

        user = get_object_or_none(User, email=email)
        if user and user.check_password(password):
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


class UserRoleView(APIView):
    '''Select role for user like distributor, delivery staff, customer'''
    permission_classes = [IsAuthenticated, IsVerified]

    def get(self, request, role):
        valid_roles = User.ROLE_CHOICES
        valid_roles = [r[0] for r in valid_roles]
        if role not in valid_roles:
            return wrap_response(False, "invalid_role", message=f"Role must be one of the following: {', '.join(valid_roles)}")
        users = User.objects.filter(role=role).values("user_id","user_name")
        return wrap_response(True, "users_retrieved", data=users, message=f"Users with role {role} retrieved successfully.")

    def post(self, request):
        user = request.user
        if user.role_accepted:
            return wrap_response(False, "role_already_accepted", message="User role already accepted")
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
            return wrap_response(True, "role_added", message="User role added successfully.")
        except User.DoesNotExist:
            return wrap_response(False, "distributor_not_found", message="Distributor not found.", status_code=status.HTTP_404_NOT_FOUND)
    
    def patch(self, request):
        user = request.user
        serializer = UserRoleSerializer(data=request.data)
        if not serializer.is_valid():
            return wrap_response(False, "invalid_data", message="Invalid data", errors=serializer.errors)
        role = serializer.validated_data.get('role')
        distributor_id = serializer.validated_data.get('distributor_id')
        try:
            user.role = role
            user.role_accepted = False
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

    def patch(self,request):
        serializer = UpdateAccountSerializer(request.user, data=request.data, partial=True)
        if not serializer.is_valid():
            return wrap_response(False, "invalid_data", message="Invalid data", errors=serializer.errors)
        serializer.save()
        return wrap_response(True, "account_updated", data=serializer.data, message="Account updated successfully.")


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
        
        reset_token = str(random.randint(100000, 999999))
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
        email = serializer.validated_data['email']
        token = serializer.validated_data['token']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return wrap_response(
                success=False,
                code="user_not_found",
                message="User not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        if user.reset_password_token!=token:
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
        

class CustomerView(APIView):
    ''' This view is for distributor to see their customers'''
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated(), IsVerified()]
        else:
            return [IsAuthenticated(), IsVerified(), DistributorPermission()]

    def get(self, request):
        user = request.user
        role_accepted = request.query_params.get('role_accepted')
        if role_accepted in ["accept", "pending"]:
            today = timezone.now().date()
            next_month_start = today.replace(day=1) + relativedelta(months=1)
            next_month_end = next_month_start + relativedelta(day=31) 
            role_accepted = True if role_accepted == "accept" else None
            # Subquery: check if order exists for that customer
            next_month_order_exists = Exists(
                Order.objects.filter(
                    customer=OuterRef("pk"),
                    date__range=(next_month_start, next_month_end)
                )
            )

            if user.role == User.DISTRIBUTOR:
                queryset = User.objects.filter(role=User.CUSTOMER, distributor=user, role_accepted=role_accepted)
            elif user.role == User.DELIVERY_STAFF:
                queryset = User.objects.filter(role=User.CUSTOMER, delivery_staff=user, role_accepted=True)
            else:
                queryset = User.objects.filter(role=User.CUSTOMER, role_accepted=role_accepted)
            customers = queryset.annotate(is_next_order = next_month_order_exists).select_related('delivery_staff').order_by('rank')
            serializer = EnrollUsersSerializer(customers, many=True)
            return wrap_response(True, "customers_list", data=serializer.data, message="Customers fetched successfully.")
        return wrap_response(False, "invalid_role_accepted", message="role_accepted must be accept or pending.")
  
    def post(self, request):
        serializer = CustomerApprovalSerializer(data=request.data)
        if serializer.is_valid():
            user_id = serializer.validated_data.get('user_id')
            delivery_staff_id = serializer.validated_data.get('delivery_staff_id')
            action = serializer.validated_data.get('action')
            if action==False:
                users = User.objects.filter(user_id=user_id, distributor=request.user, role=User.CUSTOMER).update(role_accepted=action)
            else:
                if not User.objects.filter(user_id=delivery_staff_id, role=User.DELIVERY_STAFF, role_accepted=True).exists():
                    return wrap_response(False, "invalid_delivery_staff", message="Invalid delivery staff ID.")

                users = User.objects.filter(user_id=user_id, distributor=request.user, role=User.CUSTOMER).update(role_accepted=action, delivery_staff_id=delivery_staff_id)
                if users == 0:
                    return wrap_response(False, "no_users_updated", message="No users were updated. Please check the provided user IDs.")

            return wrap_response(True, "role_accepted", message="Customer role accepted successfully.")
        return wrap_response(False, "invalid_data", message="Invalid data", errors=serializer.errors)
    
class DeliveryStaffView(APIView):
    ''' This view is for Admin/distributor to see their delivery staff'''
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated(), IsVerified(), AdminOrDistributorPermission()]
        else:
            return [IsAuthenticated(), IsVerified(), DistributorPermission()]
        
    def get(self, request):
        user = request.user
        role_accepted = request.query_params.get('role_accepted')
        distributor_id = request.query_params.get('distributor_id')
        if role_accepted in ["accept", "pending"]:
            role_accepted = True if role_accepted == "accept" else None
            if user.role == User.DISTRIBUTOR:
                customers = User.objects.filter(role=User.DELIVERY_STAFF, distributor=user, role_accepted=role_accepted).order_by('-created')
            elif distributor_id:
                customers = User.objects.filter(role=User.DELIVERY_STAFF, distributor_id=distributor_id, role_accepted=role_accepted).order_by('-created')
            else:
                return wrap_response(False, "distributor_id_required", message=" distributor_id must be required for admin.")
            serializer = EnrollUsersSerializer(customers, many=True)
            return wrap_response(True, "staff_list", data=serializer.data, message="Staff fetched successfully.")
        return wrap_response(False, "invalid_role_accepted", message="role_accepted must be accept or pending.")
    
    def post(self, request):
        serializer = UserApprovalSerializer(data=request.data)
        if serializer.is_valid():
            user_id = serializer.validated_data.get('user_id')
            action = serializer.validated_data.get('action')
            users = User.objects.filter(user_id=user_id, distributor=request.user, role=User.DELIVERY_STAFF).update(role_accepted=action)
            if users == 0:
                return wrap_response(False, "no_users_updated", message="No users were updated. Please check the provided user IDs.")

            return wrap_response(True, "role_accepted", message="Delivery role accepted successfully.")    
        return wrap_response(False, "invalid_data", message="Invalid data", errors=serializer.errors)

class DistributorView(APIView):
    ''' This view is for admin to approve/reject distributors'''
    permission_classes = [IsAuthenticated, IsVerified, AdminUserPermission]
    def get(self, request):
        role_accepted = request.query_params.get('role_accepted')
        if role_accepted in ["accept", "pending"]:
            role_accepted = True if role_accepted == "accept" else None
            users = User.objects.filter(role=User.DISTRIBUTOR, role_accepted=role_accepted).order_by('-created')
            serializer = EnrollUsersSerializer(users, many=True)
            return wrap_response(True, "distributors_list", data=serializer.data, message="Distributors fetched successfully.")
        return wrap_response(False, "invalid_role_accepted", message="role_accepted must be accept or pending.")

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

class ChangePasswordView(APIView):
    """
    Allows authenticated users to change their password by providing the old password.
    """
    permission_classes = [IsAuthenticated,IsVerified]

    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return wrap_response(success=True, code="password_changed", message="Password changed successfully.")
        return wrap_response(success=False, code="invalid_data", errors=serializer.errors)


# Distributor Add customers without email verification    
class AddCustomer(APIView):
    permission_classes = [IsAuthenticated, DistributorPermission]
    def post(self, request):
        serializer = AddCustomerSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            user_name = serializer.validated_data.get('user_name')
            password = serializer.validated_data.get('password')
            confirm_password = serializer.validated_data.get('confirm_password')
            delivery_staff = serializer.validated_data.get('delivery_staff')
            if password != confirm_password:
                return wrap_response(False, "password_mismatch", message="Password and Confirm Password do not match.")
            if User.objects.filter(Q(email=email) | Q(user_name=user_name)).exists():
                return wrap_response(False, "user_exists", 
                                        message="A user with this email and username already exists.", 
                                        status_code=status.HTTP_400_BAD_REQUEST
                                        )
            user = User.objects.create_user(
                    email=email,
                    user_name=user_name,
                    password=password,
                    is_email_verified=True,
                    role=User.CUSTOMER,
                    role_accepted=True,
                    distributor=request.user,
                    delivery_staff=delivery_staff,
                    mobile=serializer.validated_data.get('mobile'),
                    first_name=serializer.validated_data.get('first_name'),
                    last_name=serializer.validated_data.get('last_name'),
                    country=serializer.validated_data.get('country'),
                    state=serializer.validated_data.get('state'),
                    city=serializer.validated_data.get('city'),
                    address=serializer.validated_data.get('address'),
                    pin_code=serializer.validated_data.get('pin_code')
                )
            return wrap_response(True, "user_added", message="User added successfully.")
        return wrap_response(False, "invalid_data", message="Invalid data", errors=serializer.errors)


class RouteSetupView(APIView):
    permission_classes = [IsAuthenticated, IsVerified]
    def post(self, request):
        serializer = RouteSetupSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return wrap_response(False, "invalid_data", message="Invalid data", errors=serializer.errors)
        delivery_staff_id = serializer.validated_data["delivery_staff_id"] if request.user.role != User.DELIVERY_STAFF else request.user.user_id
        customers_data = serializer.validated_data["customers"]

        customer_ids = [c["id"] for c in customers_data]
        existing_customers = list(
            User.objects.filter(
                user_id__in=customer_ids,
                delivery_staff_id=delivery_staff_id,
                role=User.CUSTOMER
            )
        )

        if len(existing_customers) != len(customer_ids):
            return wrap_response(False, "customers_not_found", message="One or more customers not found for this delivery staff.")

        # map customer ranks
        rank_map = {c["id"]: c["rank"] for c in customers_data}

        # assign ranks in memory
        for customer in existing_customers:
            customer.rank = rank_map[customer.user_id]

        # ✅ bulk update ranks in single query
        with transaction.atomic():
            User.objects.bulk_update(existing_customers, ["rank"])

        return wrap_response(True, "customer_ranks_updated", message="Customer ranks updated successfully.")

class UpdateCustomerDelievery(APIView):
    "Distributor & admin update customer delivery staff"
    permission_classes = [IsAuthenticated, IsVerified, AdminOrDistributorPermission]
    def patch(self,request):
        delivery_staff_id = request.data.get('delivery_staff_id')
        customer_id = request.data.get('customer_id')
        if not delivery_staff_id or not customer_id:
            return wrap_response(False, "invalid_data", message="Invalid data", errors="delivery_staff_id or customer_id is missing")
        customer = User.objects.filter(user_id=customer_id, role=User.CUSTOMER).first()
        if not customer:
            return wrap_response(False, "customer_not_found", message="Customer not found")
        customer.delivery_staff_id = delivery_staff_id
        customer.rank = 0
        customer.save()
        return wrap_response(True, "customer_delivery_staff_updated", message="Customer delivery staff updated successfully")

class ActiveDeactiveCustomer(APIView):
    permission_classes = [IsAuthenticated, IsVerified, AdminOrDistributorPermission]

    def post(self,request):
        active = request.data.get('active')
        if type(active) != bool:
            return wrap_response(False, "active_invalid", message="active must be boolean value")
        customer_id = request.data.get('customer_id')
        updated = User.objects.filter(user_id=customer_id).update(is_active=active)
        flag = 'activate' if active else 'deactivate'
        if not updated:
            return wrap_response(False, "customer_not_found", message="Customer Not found")
        return wrap_response(True, f"customer_{flag}", message=f"Customer {flag} successfully")

    def get(self,request):
        customers = User.objects.filter(is_active=False, role = User.CUSTOMER)
        serializer = EnrollUsersSerializer(customers, many=True)
        return wrap_response(True, code='customer_retrieve', data=serializer.data)

class ActiveDeactivateDeliveryStaff(APIView):
    permission_classes = [IsAuthenticated, DistributorPermission]

    def post(self, request):
        distributor = request.user
        active = request.data.get("active")
        staff_id = request.data.get("delivery_staff_id")          # Staff to deactivate
        new_staff_id = request.data.get("new_delivery_staff_id")  # New staff for reassigning customers
        
        if type(active) != bool:
            return wrap_response(False, "active_invalid", message="active must be boolean value")
        
        if active:
            updated = User.objects.filter(user_id=staff_id).update(is_active=True)
            if not updated:
                return wrap_response(False, "delivery_staff_not_found", message="delivery_staff not found")
            return wrap_response(True, f"customer_activate", message=f"Customer activate successfully")

        
        # Validation 1: Staff IDs must be provided
        if not staff_id or not new_staff_id:
            return wrap_response(False, "missing_fields",
                                 message="delivery_staff_id and new_delivery_staff_id are required.")


        if old_staff.user_id == new_staff.user_id:
            return wrap_response(False, "same_staff",
                                 message="Old and new delivery staff cannot be same.")

        staff = User.objects.filter(
            user_id__in=[staff_id,new_staff_id],
            role=User.DELIVERY_STAFF,
            distributor=distributor,
            is_active=True
        )
        if len(staff) != 2:
            return wrap_response(False, code='missing_data', message='delivery_staff_id and new_delivery_staff_id is Invalid')

        # Cannot self assign (same staff)

        # ---------------------------------------------------
        # Reassign customers in ONE bulk update (Optimized)
        # ---------------------------------------------------
        User.objects.filter(
            role=User.CUSTOMER,
            delivery_staff=old_staff,
            distributor=distributor
        ).update(delivery_staff=new_staff)

        # ---------------------------------------------------
        # Deactivate old staff
        # ---------------------------------------------------
        old_staff.is_active = False
        old_staff.save(update_fields=["is_active"])

        return wrap_response(
            True,
            "delivery_staff_deactivated",
            message=f"Delivery staff '{old_staff.user_name}' deactivated and customers reassigned to '{new_staff.user_name}'."
        )

    def get(self,request):
        customers = User.objects.filter(is_active=False, role = User.DELIVERY_STAFF)
        serializer = EnrollUsersSerializer(customers, many=True)
        return wrap_response(True, code='customer_retrieve', data=serializer.data)


class AddPayment(APIView):
    permission_classes = [IsAuthenticated, IsVerified, AdminOrDistributorPermission]

    def post(self,request):
        user = request.user
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            if user.role == User.DISTRIBUTOR:
                if serializer.validated_data['user'].distributor != user:
                    return wrap_response(False, code='invalid_customer', message='Payement Add Failed')
            serializer.save(record_by=request.user)
            return wrap_response(True, code='payment_added_successfully', message='Payement Added Successfully')
        return wrap_response(False, code='invalid_data', message='Payement Add Failed', errors=serializer.errors)


class CustomerBalanceView(APIView):
    permission_classes = [IsAuthenticated, IsVerified]

    def get(self,request): 
        customer_id = request.query_params.get('customer_id')
        if customer_id:
            user = User.objects.filter(user_id=customer_id)
            if not user.exists():
                return wrap_response(False, code='customer_not_found', message="Customer not found")
            user = user.first()
        else:
            user = request.user
        bill_amount = user.orders.filter(
            status=Order.DELIVERED
        ).aggregate(total=Sum('total_price'))['total'] or 0

        payment_amount = user.payment_transactions.aggregate(
            total=Sum('amount')
        )['total'] or 0

        balance = payment_amount - bill_amount
        return wrap_response(True, code='balance_retrieve', data={"balance" : balance})

class DistributorBalanceView(APIView):
    permission_classes = [IsAuthenticated, IsVerified, AdminOrDistributorPermission]

    def get(self,request): 
        distributor_id = request.query_params.get('distributor_id')
        if distributor_id:
            user = User.objects.filter(user_id=distributor_id)
            if not user.exists():
                return wrap_response(False, code='distributor_not_found', message="Distributor not found")
            user = user.first()
        else:
            user = request.user
        bill_amount = user.distributor_orders.all().aggregate(total=Sum('total_price'))['total'] or 0

        payment_amount = user.payment_transactions.aggregate(
            total=Sum('amount')
        )['total'] or 0

        balance = payment_amount - bill_amount
        return wrap_response(True, code='balance_retrieve', data={"balance" : balance})


class QrCodeView(APIView):
    permission_classes = [IsAuthenticated, IsVerified,]

    def get_object(self, user):
        return getattr(user, "qr_code", None)

    def get(self, request):
        qr_obj = self.get_object(request.user)
        if not qr_obj:
            return wrap_response(False, code='qrcode_not_found', message="QR code not found")

        serializer = QrCodeSerializer(qr_obj)
        return wrap_response(True, code='qr_retrieve', data=serializer.data)

    def post(self, request):
        if self.get_object(request.user):
            return wrap_response(False, code='qrcode_not_found', message="QR code not found")

        serializer = QrCodeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return wrap_response(True, code='qrcode_created', data=serializer.data)

        return wrap_response(False, code='invalid_data', errors=serializer.errors)

    def put(self, request):
        qr_obj = self.get_object(request.user)
        if not qr_obj:
            return wrap_response(False, code='qrcode_not_found', message="QR code not found")

        serializer = QrCodeSerializer(qr_obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return wrap_response(True, code='qrcode_updated', data=serializer.data)

        return wrap_response(False, code='invalid_data', errors=serializer.errors)

    def delete(self, request):
        qr_obj = self.get_object(request.user)
        if not qr_obj:
            return wrap_response(False, code='qrcode_not_found', message="QR code not found")

        qr_obj.delete()
        return wrap_response(False, code='qrcode_deleted', message="QR deleted successfully")