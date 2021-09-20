from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subaccount', '0025_meta_options'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='subaccount',
            name='budget',
        ),
    ]
