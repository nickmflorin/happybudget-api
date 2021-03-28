from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('budget_item', '0002_budget_item_group'),
        ('subaccount', '0006_remove_subaccount_group'),
    ]

    operations = [
        migrations.AddField(
            model_name='budgetitem',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='children', to='budget_item.budgetitemgroup'),
        ),
    ]
