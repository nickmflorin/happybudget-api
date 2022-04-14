from django.urls import path, include

from .site import site


urlpatterns = [
    path('grappelli/', include('grappelli.urls')),
    path('admin/', site.urls),
    path('_nested_admin/', include('nested_admin.urls')),
]
