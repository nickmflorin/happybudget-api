from django.urls import path

from .views import TokenValidateView, TokenRefreshView

app_name = 'jwt'

urlpatterns = [
    path('refresh/', TokenRefreshView.as_view(), name='refresh'),
    path('validate/', TokenValidateView.as_view(), name='validate'),
]
