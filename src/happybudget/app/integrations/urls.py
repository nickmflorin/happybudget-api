from django.urls import path, include

app_name = 'integrations'

urlpatterns = [
    path('plaid/', include('happybudget.app.integrations.plaid.urls')),
]
