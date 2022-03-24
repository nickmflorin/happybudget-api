from django.apps import AppConfig


class FringeConfig(AppConfig):
    name = 'greenbudget.app.fringe'
    verbose_name = "Fringe"
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        # pylint: disable=import-outside-toplevel,unused-import
        import greenbudget.app.fringe.signals  # noqa
