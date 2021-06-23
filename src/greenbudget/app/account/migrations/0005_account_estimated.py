from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0004_alter_meta'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='estimated',
            field=models.FloatField(default=0.0),
        ),
    ]
