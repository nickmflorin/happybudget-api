from django.contrib import admin
from django.conf import settings
from django.urls import path, include


admin.site.site_url = settings.FRONTEND_URL


urlpatterns = [
    path('grappelli/', include('grappelli.urls')),
    path('admin/', admin.site.urls),
    path('_nested_admin/', include('nested_admin.urls')),
]
