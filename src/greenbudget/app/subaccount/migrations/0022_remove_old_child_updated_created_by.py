from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subaccount', '0021_copy_child_created_updated_by_to_parent'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='budgetsubaccount',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='budgetsubaccount',
            name='updated_by',
        ),
        migrations.RemoveField(
            model_name='templatesubaccount',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='templatesubaccount',
            name='updated_by',
        ),
    ]
