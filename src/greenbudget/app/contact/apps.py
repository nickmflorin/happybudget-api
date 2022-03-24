from django.apps import AppConfig


class ContactConfig(AppConfig):
    name = 'greenbudget.app.contact'
    verbose_name = "Contact"
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        # pylint: disable=import-outside-toplevel,unused-import
        import greenbudget.app.contact.signals  # noqa
