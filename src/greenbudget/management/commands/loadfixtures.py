from django.core import management
from django.conf import settings
from greenbudget.management.base import CustomCommand


class Command(CustomCommand):
    def handle(self, **options):
        for fixture in settings.FIXTURES:
            management.call_command("loaddata", fixture)
