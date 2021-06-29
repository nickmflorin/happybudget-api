from django.apps import AppConfig


class FringeConfig(AppConfig):
    name = 'greenbudget.app.fringe'
    verbose_name = "Fringe"

    def ready(self):
        import greenbudget.app.fringe.signals  # noqa
