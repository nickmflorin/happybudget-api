from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0011_admin_related_changes'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='is_admin',
        ),
        migrations.AlterField(
            model_name='user',
            name='date_joined',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Date Joined'),
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(max_length=254, unique=True, verbose_name='Email Address'),
        ),
        migrations.AlterField(
            model_name='user',
            name='first_name',
            field=models.CharField(max_length=150, verbose_name='Fist Name'),
        ),
        migrations.AlterField(
            model_name='user',
            name='is_active',
            field=models.BooleanField(default=True, help_text="Designates whether this user's account is disabled.", verbose_name='Active'),
        ),
        migrations.AlterField(
            model_name='user',
            name='is_staff',
            field=models.BooleanField(default=False, help_text='Designates whether this user can login to the admin site.', verbose_name='Staff'),
        ),
        migrations.AlterField(
            model_name='user',
            name='is_superuser',
            field=models.BooleanField(default=False, help_text='Designates whether this user is a superuser.', verbose_name='Superuser'),
        ),
        migrations.AlterField(
            model_name='user',
            name='last_name',
            field=models.CharField(max_length=150, verbose_name='Last Name'),
        ),
        migrations.AlterField(
            model_name='user',
            name='stripe_id',
            field=models.CharField(blank=True, editable=False, max_length=128, null=True),
        ),
    ]
