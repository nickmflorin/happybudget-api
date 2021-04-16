from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0001_initial'),
        ('fringe', '0001_initial'),
        ('subaccount', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='budgetsubaccount',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='children', to='group.budgetsubaccountgroup'),
        ),
        migrations.AddField(
            model_name='subaccount',
            name='fringes',
            field=models.ManyToManyField(to='fringe.Fringe'),
        ),
        migrations.AddField(
            model_name='templatesubaccount',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='children', to='group.templatesubaccountgroup'),
        ),
    ]
