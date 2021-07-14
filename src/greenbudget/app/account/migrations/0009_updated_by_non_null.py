from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('account', '0008_created_by_not_editable'),
    ]

    operations = [
        migrations.AlterField(
            model_name='budgetaccount',
            name='updated_by',
            field=models.ForeignKey(default=1, editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='updated_budget_accounts', to='user.user'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='templateaccount',
            name='updated_by',
            field=models.ForeignKey(default=1, editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='updated_template_accounts', to='user.user'),
            preserve_default=False,
        ),
    ]
