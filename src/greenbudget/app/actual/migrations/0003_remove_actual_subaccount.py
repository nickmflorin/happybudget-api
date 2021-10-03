from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('actual', '0002_actual_subaccount'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='actual',
            name='subaccount',
        ),
    ]
