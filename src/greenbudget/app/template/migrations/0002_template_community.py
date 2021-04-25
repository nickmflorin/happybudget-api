from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('template', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='template',
            name='community',
            field=models.BooleanField(default=False),
        ),
    ]
