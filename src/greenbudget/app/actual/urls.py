from django.urls import path, include
from rest_framework import routers

from greenbudget.app.history.urls import actual_history_urlpatterns

from .views import ActualsViewSet

app_name = "actual"

router = routers.SimpleRouter()
router.register(r'', ActualsViewSet, basename='actual')
urlpatterns = router.urls + [
    path('<int:actual_pk>/', include([
        path('history/', include(actual_history_urlpatterns)),
    ]))
]
