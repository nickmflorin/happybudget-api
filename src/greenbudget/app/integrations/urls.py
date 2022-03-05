from django.urls import path, include

app_name = 'integrations'

urlpatterns = [
    path('plaid/', include('greenbudget.app.integrations.plaid.urls')),
]
