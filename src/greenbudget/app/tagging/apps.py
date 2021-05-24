from django.apps import AppConfig


class TaggingConfig(AppConfig):
    name = 'greenbudget.app.tagging'
    verbose_name = "Tagging"

    def ready(self):
        import greenbudget.app.tagging.signals  # noqa
