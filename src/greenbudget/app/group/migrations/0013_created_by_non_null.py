from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('group', '0012_alter_meta'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='created_by',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='created_groups', to='user.user'),
            preserve_default=False,
        ),
    ]
