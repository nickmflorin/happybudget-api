from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('account', '0012_remove_old_child_updated_created_by'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='created_by_new',
            field=models.ForeignKey(default=1, editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='created_accounts', to='user.user'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='account',
            name='updated_by_new',
            field=models.ForeignKey(default=1, editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='updated_accounts', to='user.user'),
            preserve_default=False,
        ),
    ]
