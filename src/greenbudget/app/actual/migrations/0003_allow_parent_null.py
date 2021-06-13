from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('actual', '0002_put_in_budget_context'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actual',
            name='content_type',
            field=models.ForeignKey(
                limit_choices_to=models.Q(
                    models.Q(('app_label', 'account'), ('model', 'BudgetAccount')),
                    models.Q(('app_label', 'subaccount'), ('model', 'BudgetSubAccount')),
                    _connector='OR'
                ),
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='contenttypes.contenttype'
            ),
        ),
        migrations.AlterField(
            model_name='actual',
            name='object_id',
            field=models.PositiveIntegerField(null=True),
        ),
    ]
