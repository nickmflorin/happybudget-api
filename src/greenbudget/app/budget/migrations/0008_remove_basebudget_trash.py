from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0007_estimated_actual_fields'),
    ]

    # NOTE: Before this was run, we manually deleted all trash Budgets/Templates
    # because we were having problems doing it from the migration file, due
    # to polymorphic managers surrounding the Group models.
    operations = [
        migrations.RemoveField(
            model_name='basebudget',
            name='trash',
        ),
    ]
