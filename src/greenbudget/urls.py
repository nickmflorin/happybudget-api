from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

from greenbudget.conf import Environments


urlpatterns = [
    path('v1/', include('greenbudget.app.urls')),
    path('', include('greenbudget.harry.urls')),
]

if settings.ENVIRONMENT in (Environments.LOCAL, Environments.TEST):
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
