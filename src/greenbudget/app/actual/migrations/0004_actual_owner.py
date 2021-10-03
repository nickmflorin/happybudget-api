from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('actual', '0003_remove_actual_subaccount'),
    ]

    operations = [
        migrations.AddField(
            model_name='actual',
            name='content_type',
            field=models.ForeignKey(limit_choices_to=models.Q(models.Q(('app_label', 'markup'), ('model', 'Markup')), models.Q(('app_label', 'subaccount'), ('model', 'BudgetSubAccount')), _connector='OR'), null=True, on_delete=django.db.models.deletion.SET_NULL, to='contenttypes.contenttype'),
        ),
        migrations.AddField(
            model_name='actual',
            name='object_id',
            field=models.PositiveIntegerField(db_index=True, null=True),
        ),
    ]
