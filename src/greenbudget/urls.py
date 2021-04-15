from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('v1/', include('greenbudget.app.urls')),
    path('', lambda request: JsonResponse({'status': '200'})),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
