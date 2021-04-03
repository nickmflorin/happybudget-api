from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0003_fringe'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fringe',
            name='rate',
            field=models.FloatField(null=True),
        ),
    ]
