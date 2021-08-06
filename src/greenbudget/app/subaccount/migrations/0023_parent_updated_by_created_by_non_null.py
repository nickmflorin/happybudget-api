from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('subaccount', '0022_remove_old_child_updated_created_by'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subaccount',
            name='created_by_new',
            field=models.ForeignKey(default=1, editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='created_subaccounts', to='user.user'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='subaccount',
            name='updated_by_new',
            field=models.ForeignKey(default=1, editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='updated_subaccounts', to='user.user'),
            preserve_default=False,
        ),
    ]
