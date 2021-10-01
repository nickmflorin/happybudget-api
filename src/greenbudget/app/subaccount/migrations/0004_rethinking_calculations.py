from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subaccount', '0003_rethinking_calculations'),
    ]

    operations = [
        migrations.RenameField(
            model_name='subaccount',
            old_name='estimated',
            new_name='accumulated_value',
        ),
        migrations.AddField(
            model_name='subaccount',
            name='accumulated_fringe_contribution',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='subaccount',
            name='accumulated_markup_contribution',
            field=models.FloatField(default=0.0),
        ),
    ]
