from django.views.decorators.csrf import csrf_exempt
from django.urls import path

from .views import (
    LoginView, LogoutView, ResetPasswordView, ForgotPasswordView,
    SocialLoginView)

app_name = "authentication"

urlpatterns = [
    path('login/', csrf_exempt(LoginView.as_view()), name='login'),
    path('logout/', LogoutView.as_view()),
    path('reset-password/', ResetPasswordView.as_view()),
    path('forgot-password/', ForgotPasswordView.as_view()),
    path('social-login/', csrf_exempt(SocialLoginView.as_view())),
]
