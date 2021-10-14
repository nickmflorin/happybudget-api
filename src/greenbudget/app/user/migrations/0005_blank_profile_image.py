from django.db import migrations, models
import greenbudget.app.user.models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0004_non_editable_date_joined'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='profile_image',
            field=models.ImageField(blank=True, null=True, upload_to=greenbudget.app.user.models.upload_to),
        ),
    ]
