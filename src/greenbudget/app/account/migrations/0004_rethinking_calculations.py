from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0003_rethinking_calculations'),
    ]

    operations = [
        migrations.RenameField(
            model_name='account',
            old_name='fringe_contribution',
            new_name='accumulated_fringe_contribution',
        ),
        migrations.RenameField(
            model_name='account',
            old_name='estimated',
            new_name='accumulated_value',
        ),
        migrations.AddField(
            model_name='account',
            name='accumulated_markup_contribution',
            field=models.FloatField(default=0.0),
        ),
    ]
