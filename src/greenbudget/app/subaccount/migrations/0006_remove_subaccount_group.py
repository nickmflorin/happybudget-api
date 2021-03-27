from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subaccount', '0005_subaccountgroup_color'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='subaccount',
            name='group',
        ),
    ]
