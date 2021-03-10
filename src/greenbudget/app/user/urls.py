from django.views.decorators.csrf import csrf_exempt
from django.urls import path

from .views import UserRegistrationView

app_name = "user"

urlpatterns = [
    path('registration/', csrf_exempt(UserRegistrationView.as_view({
        'post': 'create',
    })))
]
