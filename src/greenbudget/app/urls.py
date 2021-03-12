from django.urls import path, include


urlpatterns = [
    path('accounts/', include('greenbudget.app.account.urls')),
    path('actuals/', include('greenbudget.app.actual.urls')),
    path('auth/', include('greenbudget.app.authentication.urls')),
    path('budgets/', include('greenbudget.app.budget.urls')),
    path('comments/', include('greenbudget.app.comment.urls')),
    path('subaccounts/', include('greenbudget.app.subaccount.urls')),
    path('jwt/', include('greenbudget.app.jwt.urls')),
    path('users/', include('greenbudget.app.user.urls')),
]
