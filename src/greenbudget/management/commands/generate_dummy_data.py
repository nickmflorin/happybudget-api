from greenbudget.management.base import CustomCommand
from greenbudget.management.dummy_data_suite import suite


class Command(CustomCommand):
    def handle(self, **options):
        suite.generate()
