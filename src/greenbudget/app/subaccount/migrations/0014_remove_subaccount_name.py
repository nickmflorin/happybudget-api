from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subaccount', '0013_estimated_actual'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='subaccount',
            name='name',
        ),
    ]
