from greenbudget.management.base import CustomCommand
from greenbudget.management.decorators import debug_only

from greenbudget.app import cache
from greenbudget.data import generate


@debug_only
class Command(CustomCommand):
    @cache.disable()
    def handle(self, **options):
        gen = generate.ApplicationDataGenerator()
        gen()
