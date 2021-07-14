from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('actual', '0006_remove_generic_parent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actual',
            name='created_by',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='created_actuals', to='user.user'),
            preserve_default=False,
        ),
    ]
