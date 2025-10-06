from django.urls import path
from .views import (UserRegistrationView, UserLoginView, EmailVerificationView,
                    SendEmailTokenView, UserLogoutView, UserProfile,UpdateFCMTokenView,
                    ForgotPasswordView, ResetPasswordView, RoleWiseUsersView
                    )
urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('logout/', UserLogoutView.as_view(), name='user-logout'),
    path('send-email-token/', SendEmailTokenView.as_view(), name='send-email-token'),
    path('verify-email/', EmailVerificationView.as_view(), name='email-verify'),
    path('profile/', UserProfile.as_view(), name='user-profile'),
    path('update-fcm-token/', UpdateFCMTokenView.as_view(), name='update-fcm-token'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('role/<str:role>/', RoleWiseUsersView.as_view(), name='role-wise-users'),
]   