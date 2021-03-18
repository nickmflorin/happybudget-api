from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('v1/', include('greenbudget.app.urls')),
    path('', lambda request: JsonResponse({'status': '200'})),
]
