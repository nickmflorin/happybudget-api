from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('subaccount', '0014_remove_subaccount_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='budgetsubaccount',
            name='created_by',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='created_budget_subaccounts', to='user.user'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='templatesubaccount',
            name='created_by',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='created_template_subaccounts', to='user.user'),
            preserve_default=False,
        ),
    ]
