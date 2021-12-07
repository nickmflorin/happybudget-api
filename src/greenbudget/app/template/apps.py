from django.apps import AppConfig


class TemplateConfig(AppConfig):
    name = 'greenbudget.app.template'
    verbose_name = "Template"
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        import greenbudget.app.template.signals  # noqa
