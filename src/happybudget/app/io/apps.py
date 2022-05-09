from django.apps import AppConfig


class IOConfig(AppConfig):
    name = 'happybudget.app.io'
    verbose_name = "IO"
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        # pylint: disable=import-outside-toplevel,unused-import
        import happybudget.app.io.signals  # noqa
