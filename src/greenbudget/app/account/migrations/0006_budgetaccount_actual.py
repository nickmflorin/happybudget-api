from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0005_account_estimated'),
    ]

    operations = [
        migrations.AddField(
            model_name='budgetaccount',
            name='actual',
            field=models.FloatField(default=0.0),
        ),
    ]
