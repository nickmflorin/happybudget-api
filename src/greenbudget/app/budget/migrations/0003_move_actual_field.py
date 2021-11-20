from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0002_rethinking_calculations'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='budget',
            name='actual',
        ),
        migrations.AddField(
            model_name='basebudget',
            name='actual',
            field=models.FloatField(default=0.0),
        ),
    ]
