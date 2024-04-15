from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    ActivateView,
    DashboardView,
    ForgotPasswordView,
    ResetPasswordValidateView,
    ResetPasswordView,
    EditProfileView,
    ChangePasswordView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('activate/<uidb64>/<token>/', ActivateView.as_view(), name='activate'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password-validate/<uidb64>/<token>/', ResetPasswordValidateView.as_view(), name='reset_password_validate'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('edit-profile/', EditProfileView.as_view(), name='edit_profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
]
