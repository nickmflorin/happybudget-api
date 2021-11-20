from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contact', '0005_rename_user_to_created_by'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_contacts', to=settings.AUTH_USER_MODEL),
        ),
    ]
