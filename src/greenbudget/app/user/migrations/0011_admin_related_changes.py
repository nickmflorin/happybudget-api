from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0010_remove_approval'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='address',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='company',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='is_active',
            field=models.BooleanField(default=True, help_text="Designates whether this user's account is disabled.", verbose_name='active'),
        ),
        migrations.AlterField(
            model_name='user',
            name='is_first_time',
            field=models.BooleanField(default=True, help_text='Designates whether this user has logged in yet.', verbose_name='First Time Login'),
        ),
        migrations.AlterField(
            model_name='user',
            name='is_verified',
            field=models.BooleanField(default=False, help_text='Designates whether this user has verified their email address.', verbose_name='Verified'),
        ),
        migrations.AlterField(
            model_name='user',
            name='phone_number',
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='position',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
    ]
