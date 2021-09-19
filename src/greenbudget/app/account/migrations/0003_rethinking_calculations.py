from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0002_rethinking_calculations'),
        ('account', '0002_add_relations'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='budgetaccount',
            name='actual',
        ),
        migrations.AddField(
            model_name='account',
            name='actual',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='account',
            name='fringe_contribution',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='account',
            name='markup_contribution',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='account',
            name='parent',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='children', to='budget.basebudget'),
        ),
    ]
