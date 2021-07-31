from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0010_phone_number_null'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='phone_number2',
            field=models.BigIntegerField(null=True),
        ),
    ]
