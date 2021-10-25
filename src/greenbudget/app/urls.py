from django.urls import path, include


urlpatterns = [
    path('accounts/', include('greenbudget.app.account.urls')),
    path('actuals/', include('greenbudget.app.actual.urls')),
    path('auth/', include('greenbudget.app.authentication.urls')),
    path('billing/', include('greenbudget.app.billing.urls')),
    path('budgets/', include('greenbudget.app.budget.urls')),
    path('contacts/', include('greenbudget.app.contact.urls')),
    path('fringes/', include('greenbudget.app.fringe.urls')),
    path('groups/', include('greenbudget.app.group.urls')),
    path('io/', include('greenbudget.app.io.urls')),
    path('markups/', include('greenbudget.app.markup.urls')),
    path('pdf/', include('greenbudget.app.pdf.urls')),
    path('subaccounts/', include('greenbudget.app.subaccount.urls')),
    path('templates/', include('greenbudget.app.template.urls')),
    path('users/', include('greenbudget.app.user.urls')),
]
