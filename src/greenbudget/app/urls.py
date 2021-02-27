from django.urls import path, include


urlpatterns = [
    path('auth/', include('greenbudget.app.authentication.urls')),
    path('budgets/', include('greenbudget.app.budget.urls')),
    path('jwt/', include('greenbudget.app.jwt.urls')),
]
