from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subaccount', '0023_parent_updated_by_created_by_non_null'),
    ]

    operations = [
        migrations.RenameField(
            model_name='subaccount',
            old_name='created_by_new',
            new_name='created_by',
        ),
        migrations.RenameField(
            model_name='subaccount',
            old_name='updated_by_new',
            new_name='updated_by',
        ),
    ]
