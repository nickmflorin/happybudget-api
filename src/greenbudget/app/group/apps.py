from django.apps import AppConfig


class GroupConfig(AppConfig):
    name = 'greenbudget.app.group'
    verbose_name = "Group"
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        import greenbudget.app.group.signals  # noqa
