from django.urls import path, include


urlpatterns = [
    path('budgets/', include('backend.app.budget.urls')),
    path('jwt/', include('backend.app.jwt.urls')),
]
