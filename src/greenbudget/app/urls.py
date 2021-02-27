from django.urls import path, include


urlpatterns = [
    path('budgets/', include('greenbudget.app.budget.urls')),
    path('jwt/', include('greenbudget.app.jwt.urls')),
]
