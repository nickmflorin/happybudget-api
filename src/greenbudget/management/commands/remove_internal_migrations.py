from django.conf import settings
from django.core import management
from django.db.migrations.recorder import MigrationRecorder

from greenbudget.management import CustomCommand, debug_only


@debug_only
class Command(CustomCommand):
    @management.base.no_translations
    def handle(self, *args, **options):
        internal_apps = [
            app.split('.')[-1] for app in settings.INSTALLED_APPS
            if app.startswith('greenbudget')
        ]
        qs = MigrationRecorder.Migration.objects.filter(
            app__in=internal_apps)
        num = qs.count()
        if num:
            self.info(f"Found {qs.count()} migrations.")
            ans = self.query_boolean("Remove?", prefix=('y/n'))
            if ans:
                qs.delete()
                self.success(f"Successfully deleted {num} migrations.")
        else:
            self.info("No migrations to remove.")
