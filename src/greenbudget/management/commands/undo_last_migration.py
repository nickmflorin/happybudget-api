from django.core import management
from django.db.migrations.recorder import MigrationRecorder

from greenbudget.management import CustomCommand, debug_only


@debug_only
class Command(CustomCommand):
    @management.base.no_translations
    def handle(self, *args, **options):
        MigrationRecorder.Migration.objects.latest('applied').delete()
