from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0002_name_user_unique_polymorphic'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('actual', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actual',
            name='budget',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='actuals', to='budget.budget'),
        ),
        migrations.AlterField(
            model_name='actual',
            name='content_type',
            field=models.ForeignKey(limit_choices_to=models.Q(models.Q(('app_label', 'account'), ('model', 'BudgetAccount')), models.Q(('app_label', 'subaccount'), ('model', 'BudgetSubAccount')), _connector='OR'), on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype'),
        ),
    ]
