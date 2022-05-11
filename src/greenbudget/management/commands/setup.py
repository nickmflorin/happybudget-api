from django.core import management

from happybudget.management import CustomCommand, askable, skippable, debug_only

from happybudget.app import cache


@debug_only
class Command(CustomCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--skip_migrate',
            action='store_true',
            help='Skip running the migrations.',
        )
        parser.add_argument(
            '--skip_reset_db',
            action='store_true',
            help='Skip resetting the database.',
        )
        parser.add_argument(
            '--skip_load_fixtures',
            action='store_true',
            help='Skip loading the fixtures.',
        )
        parser.add_argument(
            '--skip_create_superuser',
            action='store_true',
            help='Skip creating the superuser.',
        )
        parser.add_argument(
            '--email',
            dest='email',
            default=None,
            help='The email for the superuser.',
        )
        parser.add_argument(
            '--password',
            dest='password',
            default=None,
            help='The password for the superuser.',
        )

    @askable("Would you like to load fixtures?")
    @skippable("Skipping loading fixtures.")
    def load_fixtures(self, **options):
        management.call_command("loadfixtures")

    @skippable("Skipping database reset.")
    @askable(
        "Would you like to reset the database?",
        (
            "This will remove all data and schemas from the database...",
            "HTTP_INFO"
        )
    )
    def reset_db(self, **options):
        self.stdout.write("Resetting Database...",
            style_func=self.style.HTTP_NOT_FOUND)
        management.call_command("reset_db")
        return True

    @askable("Would you like to run migrations?")
    @skippable("Skipping migration.")
    def migrate(self, **options):
        management.call_command("migrate")

    @skippable("Skipping superuser creation.")
    def create_superuser(self, **options):
        management.call_command("createsuperuser")

    @management.base.no_translations
    @cache.disable()
    def handle(self, *args, **options):
        database_reset = self.reset_db(**options)
        self.migrate(ask=not database_reset, **options)
        self.load_fixtures(**options)
        management.call_command("collectstatic")
        self.create_superuser(**options)
        self.success("All setup.")
