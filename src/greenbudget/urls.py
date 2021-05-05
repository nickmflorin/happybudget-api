from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.urls import path, include

admin.site.site_header = settings.ADMIN_SITE_HEADER
admin.site.site_title = settings.ADMIN_SITE_TITLE
admin.site.index_title = settings.ADMIN_INDEX_TITLE

urlpatterns = [
    path('grappelli/', include('grappelli.urls')),
    path('admin/', admin.site.urls),
    path('v1/', include('greenbudget.app.urls')),
    path('', lambda request: JsonResponse({'status': '200'})),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
