from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0003_move_actual_field'),
    ]

    operations = [
        migrations.RenameField(
            model_name='basebudget',
            old_name='fringe_contribution',
            new_name='accumulated_fringe_contribution',
        ),
        migrations.RenameField(
            model_name='basebudget',
            old_name='markup_contribution',
            new_name='accumulated_markup_contribution',
        ),
        migrations.RenameField(
            model_name='basebudget',
            old_name='estimated',
            new_name='accumulated_value',
        ),
    ]
