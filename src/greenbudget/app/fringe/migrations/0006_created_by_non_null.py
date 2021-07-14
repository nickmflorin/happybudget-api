from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('fringe', '0005_remove_name_unique_constraint'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fringe',
            name='created_by',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='created_fringes', to='user.user'),
            preserve_default=False,
        ),
    ]
