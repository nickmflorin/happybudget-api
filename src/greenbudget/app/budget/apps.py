from django.apps import AppConfig


class BudgetConfig(AppConfig):
    name = 'greenbudget.app.budget'
    verbose_name = "Budget"
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        # pylint: disable=import-outside-toplevel,unused-import
        import greenbudget.app.budget.signals  # noqa
