from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subaccount', '0010_remove_subaccount_unit'),
    ]

    operations = [
        migrations.RenameField(
            model_name='subaccount',
            old_name='unit_new',
            new_name='unit',
        ),
    ]
