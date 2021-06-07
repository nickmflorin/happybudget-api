from django.apps import AppConfig


class BudgetConfig(AppConfig):
    name = 'greenbudget.app.budget'
    verbose_name = "Budget"

    def ready(self):
        import greenbudget.app.budget.signals  # noqa
