from django.core import management
from greenbudget.management.base import CustomCommand

FIXTURES = []


class Command(CustomCommand):
    def handle(self, **options):
        for fixture in FIXTURES:
            management.call_command("loaddata", fixture)