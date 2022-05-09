from django.urls import path, include


urlpatterns = [
    path('accounts/', include('happybudget.app.account.urls')),
    path('actuals/', include('happybudget.app.actual.urls')),
    path('auth/', include('happybudget.app.authentication.urls')),
    path('billing/', include('happybudget.app.billing.urls')),
    path('budgets/', include('happybudget.app.budget.urls')),
    path('collaborators/', include('happybudget.app.collaborator.urls')),
    path('contacts/', include('happybudget.app.contact.urls')),
    path('fringes/', include('happybudget.app.fringe.urls')),
    path('groups/', include('happybudget.app.group.urls')),
    path('integrations/', include('happybudget.app.integrations.urls')),
    path('io/', include('happybudget.app.io.urls')),
    path('markups/', include('happybudget.app.markup.urls')),
    path('pdf/', include('happybudget.app.pdf.urls')),
    path('subaccounts/', include('happybudget.app.subaccount.urls')),
    path('templates/', include('happybudget.app.template.urls')),
    path('users/', include('happybudget.app.user.urls')),
]
