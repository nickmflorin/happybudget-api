from django.apps import AppConfig


class TaggingConfig(AppConfig):
    name = 'greenbudget.app.tagging'
    verbose_name = "Tagging"
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        # pylint: disable=import-outside-toplevel,unused-import
        import greenbudget.app.tagging.signals  # noqa
