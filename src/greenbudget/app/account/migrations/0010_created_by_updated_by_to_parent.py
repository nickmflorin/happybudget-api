from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('account', '0009_updated_by_non_null'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='created_by_new',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='created_accounts', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='account',
            name='updated_by_new',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='updated_accounts', to=settings.AUTH_USER_MODEL),
        ),
    ]
