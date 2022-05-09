from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_order_by_last_login'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='has_password',
            field=models.BooleanField(default=True, editable=False, help_text='Designates whether or not the user was authenticated with social login.', verbose_name='Has Password'),
        ),
        migrations.AlterField(
            model_name='user',
            name='password',
            field=models.CharField(max_length=128, verbose_name='Password'),
        ),
    ]
