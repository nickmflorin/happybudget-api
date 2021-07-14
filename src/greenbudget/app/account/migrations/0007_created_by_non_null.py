from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('account', '0006_budgetaccount_actual'),
    ]

    operations = [
        migrations.AlterField(
            model_name='budgetaccount',
            name='created_by',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='created_budget_accounts', to='user.user'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='templateaccount',
            name='created_by',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='created_template_accounts', to='user.user'),
            preserve_default=False,
        ),
    ]
