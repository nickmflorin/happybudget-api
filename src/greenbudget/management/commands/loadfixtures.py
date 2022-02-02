from django.core import management
from django.conf import settings

from greenbudget.management.base import CustomCommand

from greenbudget.app import cache


class Command(CustomCommand):
    @cache.disable()
    def handle(self, **options):
        for fixture in settings.FIXTURES:
            management.call_command("loaddata", fixture)
