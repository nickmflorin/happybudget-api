from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
        ('budget', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='basebudget',
            unique_together={('created_by', 'name', 'polymorphic_ctype_id')},
        ),
    ]