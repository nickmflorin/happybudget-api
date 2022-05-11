from django.apps import AppConfig


class FringeConfig(AppConfig):
    name = 'happybudget.app.fringe'
    verbose_name = "Fringe"
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        # pylint: disable=import-outside-toplevel,unused-import
        import happybudget.app.fringe.signals  # noqa
