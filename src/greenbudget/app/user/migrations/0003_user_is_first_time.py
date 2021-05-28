from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_user_profile_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_first_time',
            field=models.BooleanField(default=True),
        ),
    ]
