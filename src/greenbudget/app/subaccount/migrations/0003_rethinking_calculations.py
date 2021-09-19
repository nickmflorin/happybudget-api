from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subaccount', '0002_add_relations'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='budgetsubaccount',
            name='actual',
        ),
        migrations.AddField(
            model_name='subaccount',
            name='actual',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='subaccount',
            name='fringe_contribution',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='subaccount',
            name='markup_contribution',
            field=models.FloatField(default=0.0),
        ),
    ]
