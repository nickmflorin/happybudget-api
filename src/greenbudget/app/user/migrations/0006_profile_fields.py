from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0005_blank_profile_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='address',
            field=models.CharField(max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='company',
            field=models.CharField(max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='phone_number',
            field=models.BigIntegerField(null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='position',
            field=models.CharField(max_length=128, null=True),
        ),
    ]
