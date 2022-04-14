from django.db import migrations


def forwards_func(apps, schema_editor):
    # Before we can change the updated_by field to a non-nullable field, we
    # have to set the updated by user to the user that created the budget.
    BaseBudget = apps.get_model("budget", "BaseBudget")
    User = apps.get_model("user", "User")
    db_alias = schema_editor.connection.alias

    budgets_to_update = []
    for budget in BaseBudget.objects.filter(updated_by=None):
        try:
            budget.updated_by = budget.created_by
        except User.DoesNotExist:
            pass
        else:
            budgets_to_update.append(budget)

    BaseBudget.objects.using(db_alias).bulk_update(
        budgets_to_update, fields=['updated_by'])


class Migration(migrations.Migration):
    dependencies = [
        ('budget', '0003_updated_by'),
    ]

    operations = [
        migrations.RunPython(forwards_func),
    ]
