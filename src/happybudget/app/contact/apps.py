from django.apps import AppConfig


class ContactConfig(AppConfig):
    name = 'happybudget.app.contact'
    verbose_name = "Contact"
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        # pylint: disable=import-outside-toplevel,unused-import
        import happybudget.app.contact.signals  # noqa
