from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('subaccount', '0019_unit_color_blank'),
    ]

    operations = [
        migrations.AddField(
            model_name='subaccount',
            name='created_by_new',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='created_subaccounts', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='subaccount',
            name='updated_by_new',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='updated_subaccounts', to=settings.AUTH_USER_MODEL),
        ),
    ]
