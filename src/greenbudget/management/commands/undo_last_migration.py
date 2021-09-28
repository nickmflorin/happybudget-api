from django.core import management
from django.db.migrations.recorder import MigrationRecorder

from greenbudget.management.base import CustomCommand
from greenbudget.management.decorators import debug_only


@debug_only
class Command(CustomCommand):
    @management.base.no_translations
    def handle(self, *args, **options):
        MigrationRecorder.Migration.objects.latest('applied').delete()
