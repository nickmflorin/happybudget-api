from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('user', '0003_has_password'),
        ('budget', '0002_budget_archived'),
    ]

    operations = [
        migrations.AddField(
            model_name='basebudget',
            name='updated_by',
            field=models.ForeignKey(
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='updated_budgets',
                to='user.user'
            ),
        ),
    ]
