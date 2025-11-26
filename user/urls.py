from django.urls import path
from .views import (UserRegistrationView, UserLoginView, EmailVerificationView, UserRoleView,
                    SendEmailTokenView, UserLogoutView,UpdateFCMTokenView,ForgotPasswordView,
                    ResetPasswordView, AccountView,DistributorView, CustomerView , DeliveryStaffView, DistributorView,
                    ChangePasswordView,AddCustomer,RouteSetupView,UpdateCustomerDelievery, ActiveDeactiveCustomer, ActiveDeactiveCustomer, ActiveDeactivateDeliveryStaff
                    )
urlpatterns = [
    path('register/', UserRegistrationView.as_view()),
    path('login/', UserLoginView.as_view()),
    path('logout/', UserLogoutView.as_view()),
    path('send-email-token/', SendEmailTokenView.as_view()),
    path('verify-email/', EmailVerificationView.as_view()),
    path('role/', UserRoleView.as_view()),
    path('role/<str:role>/', UserRoleView.as_view()),
    path('account/', AccountView.as_view()),
    path('update-fcm-token/', UpdateFCMTokenView.as_view()),
    path('forgot-password/', ForgotPasswordView.as_view()),
    path('reset-password/', ResetPasswordView.as_view()),
    path('change-password/', ChangePasswordView.as_view()),
    path('customers/', CustomerView.as_view()),
    path('delivery-staff/', DeliveryStaffView.as_view()),
    path('distributors/', DistributorView.as_view()),
    path('add_customer/', AddCustomer.as_view()),
    path('route_setup/', RouteSetupView.as_view()),
    path('update_customer_delievery/', UpdateCustomerDelievery.as_view()),
    path('active-deactive-customer', ActiveDeactiveCustomer.as_view()),
    path('active-deactive-delievery_staff', ActiveDeactivateDeliveryStaff.as_view()),

]