from django.core import management
from django.db.migrations.recorder import MigrationRecorder

from happybudget.management import CustomCommand, debug_only


@debug_only
class Command(CustomCommand):
    def add_arguments(self, parser):
        parser.add_argument('--app')

    @management.base.no_translations
    def handle(self, *args, **options):
        deleted = 0
        for migration in MigrationRecorder.Migration.objects.all():
            if options['app'] is None or options['app'] == migration.app:
                deleted += 1
                migration.delete()

        if deleted == 0:
            self.info("No migrations to drop.")
            return

        self.success("Successfully dropped %s migrations." % deleted)
