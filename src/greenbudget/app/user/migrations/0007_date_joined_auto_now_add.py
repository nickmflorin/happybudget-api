from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0006_profile_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='date_joined',
            field=models.DateTimeField(auto_now_add=True, verbose_name='date joined'),
        ),
    ]
