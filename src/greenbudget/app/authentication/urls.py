from django.views.decorators.csrf import csrf_exempt
from django.urls import path

from .views import LoginView, LogoutView

app_name = "authentication"

urlpatterns = [
    path('login/', csrf_exempt(LoginView.as_view())),
    path('logout/', LogoutView.as_view()),
]
