from django.urls import path
from .views import (UserRegistrationView, UserLoginView, EmailVerificationView, UserRoleView,
                    SendEmailTokenView, UserLogoutView, UserProfile,UpdateFCMTokenView,ForgotPasswordView,
                    ResetPasswordView, RoleWiseUsersView,AccountView,DistributorView, CustomersView , DeliveryStaffView, DistributorView,
                    ChangePasswordView,ChangeNotificationModeView,
                    )
urlpatterns = [
    path('register/', UserRegistrationView.as_view()),
    path('login/', UserLoginView.as_view()),
    path('logout/', UserLogoutView.as_view()),
    path('send-email-token/', SendEmailTokenView.as_view()),
    path('verify-email/', EmailVerificationView.as_view()),
    path('role/', UserRoleView.as_view()),
    path('profile/', UserProfile.as_view()),
    path('account/', AccountView.as_view()),
    path('update-fcm-token/', UpdateFCMTokenView.as_view()),
    path('forgot-password/', ForgotPasswordView.as_view()),
    path('reset-password/', ResetPasswordView.as_view()),
    path('change-password/', ChangePasswordView.as_view()),
    path('role/<str:role>/', RoleWiseUsersView.as_view()),
    path('customers/', CustomersView.as_view()),
    path('delivery-staff/', DeliveryStaffView.as_view()),
    path('distributors/', DistributorView.as_view()),
<<<<<<< HEAD
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path("ask-permission/", AskPermissionView.as_view(), name="ask-permission"),
    path("answer-permission/", AnswerPermissionView.as_view(), name="answer-permission"),
=======
    path("change-notification-mode/", ChangeNotificationModeView.as_view()),
>>>>>>> main

]