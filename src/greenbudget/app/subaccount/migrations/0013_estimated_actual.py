from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subaccount', '0012_alter_meta'),
    ]

    operations = [
        migrations.AddField(
            model_name='budgetsubaccount',
            name='actual',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='subaccount',
            name='estimated',
            field=models.FloatField(default=0.0),
        ),
    ]
