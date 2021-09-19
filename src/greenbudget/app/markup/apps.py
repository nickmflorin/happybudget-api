from django.apps import AppConfig


class MarkupConfig(AppConfig):
    name = 'greenbudget.app.markup'
    verbose_name = "Markup"

    def ready(self):
        import greenbudget.app.markup.signals  # noqa
