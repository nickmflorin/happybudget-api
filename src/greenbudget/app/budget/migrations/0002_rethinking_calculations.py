from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='basebudget',
            name='fringe_contribution',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='basebudget',
            name='markup_contribution',
            field=models.FloatField(default=0.0),
        ),
    ]
