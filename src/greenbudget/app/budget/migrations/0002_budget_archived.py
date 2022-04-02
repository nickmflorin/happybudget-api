from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='budget',
            name='archived',
            field=models.BooleanField(default=False),
        ),
    ]
