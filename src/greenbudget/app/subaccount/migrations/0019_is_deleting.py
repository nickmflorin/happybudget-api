from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subaccount', '0018_moving_fields_to_base'),
    ]

    operations = [
        migrations.AddField(
            model_name='subaccount',
            name='is_deleting',
            field=models.BooleanField(default=False),
        ),
    ]
