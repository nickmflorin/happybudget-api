from django.apps import AppConfig


class ContactConfig(AppConfig):
    name = 'greenbudget.app.contact'
    verbose_name = "Contact"

    def ready(self):
        import greenbudget.app.contact.signals  # noqa
