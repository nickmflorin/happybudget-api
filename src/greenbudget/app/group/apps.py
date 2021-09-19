from django.apps import AppConfig


class GroupConfig(AppConfig):
    name = 'greenbudget.app.group'
    verbose_name = "Group"

    def ready(self):
        import greenbudget.app.group.signals  # noqa
