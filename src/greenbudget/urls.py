from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.urls import path, include

from greenbudget.conf import Environments

urlpatterns = [
    path('grappelli/', include('grappelli.urls')),
    path('admin/', admin.site.urls),
    path('v1/', include('greenbudget.app.urls')),
    path('', lambda request: JsonResponse({'status': '200'})),
]

if settings.ENVIRONMENT == Environments.LOCAL:
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT)
