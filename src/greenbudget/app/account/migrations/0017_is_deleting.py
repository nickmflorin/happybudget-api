from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0016_moving_fields_to_base'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='is_deleting',
            field=models.BooleanField(default=False),
        ),
    ]
