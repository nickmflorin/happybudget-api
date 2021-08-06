from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0011_copy_child_created_updated_by_to_parent'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='budgetaccount',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='budgetaccount',
            name='updated_by',
        ),
        migrations.RemoveField(
            model_name='templateaccount',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='templateaccount',
            name='updated_by',
        ),
    ]
