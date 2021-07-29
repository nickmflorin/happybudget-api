from django.apps import AppConfig


class PdfConfig(AppConfig):
    name = 'greenbudget.app.pdf'
    verbose_name = "Pdf"

    def ready(self):
        import greenbudget.app.pdf.signals  # noqa
