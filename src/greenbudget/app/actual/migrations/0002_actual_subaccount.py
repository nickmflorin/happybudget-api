from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('subaccount', '0001_initial'),
        ('actual', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='actual',
            name='subaccount',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='actuals', to='subaccount.budgetsubaccount'),
        ),
    ]
