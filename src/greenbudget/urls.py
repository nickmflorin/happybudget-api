from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

from greenbudget.conf import Environments


admin.site.site_url = settings.FRONTEND_URL


urlpatterns = [
    path('grappelli/', include('grappelli.urls')),
    path('admin/', admin.site.urls),
    path('v1/', include('greenbudget.app.urls')),
]

if settings.ENVIRONMENT in (Environments.LOCAL, Environments.TEST):
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
