from greenbudget.management import CustomCommand, debug_only

from greenbudget.data import generate_users


@debug_only
class Command(CustomCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forces the recreation of the dummy users.',
        )

    def handle(self, **options):
        gen = generate_users.UserGenerator(self)
        gen(force=options['force'])
