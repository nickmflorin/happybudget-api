from django.apps import AppConfig


class TemplateConfig(AppConfig):
    name = 'greenbudget.app.template'
    verbose_name = "Template"

    def ready(self):
        import greenbudget.app.template.signals  # noqa
