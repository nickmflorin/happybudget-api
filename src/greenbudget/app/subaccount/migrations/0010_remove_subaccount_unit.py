from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subaccount', '0009_migrate_units_to_model'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='subaccount',
            name='unit',
        ),
    ]
