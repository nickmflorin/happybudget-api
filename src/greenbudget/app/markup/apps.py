from django.apps import AppConfig


class MarkupConfig(AppConfig):
    name = 'greenbudget.app.markup'
    verbose_name = "Markup"
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        # pylint: disable=import-outside-toplevel,unused-import
        import greenbudget.app.markup.signals  # noqa
