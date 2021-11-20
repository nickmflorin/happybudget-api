from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('subaccount', '0013_latest_by_order'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='subaccount',
            unique_together={('content_type', 'object_id', 'order')},
        ),
    ]
