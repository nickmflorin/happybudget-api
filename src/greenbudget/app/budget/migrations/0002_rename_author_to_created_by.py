from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('budget', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='budget',
            old_name='author',
            new_name='created_by',
        ),
        migrations.AlterUniqueTogether(
            name='budget',
            unique_together={('created_by', 'name')},
        ),
    ]
