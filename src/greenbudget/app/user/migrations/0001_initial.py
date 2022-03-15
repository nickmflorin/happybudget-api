from django.db import migrations, models
import greenbudget.app.user.managers
import greenbudget.app.user.models
import timezone_field.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('first_name', models.CharField(max_length=150, verbose_name='First Name')),
                ('last_name', models.CharField(max_length=150, verbose_name='Last Name')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='Email Address')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('date_joined', models.DateTimeField(auto_now_add=True, verbose_name='Date Joined')),
                ('position', models.CharField(blank=True, max_length=128, null=True)),
                ('company', models.CharField(blank=True, max_length=128, null=True)),
                ('address', models.CharField(blank=True, max_length=30, null=True)),
                ('phone_number', models.BigIntegerField(blank=True, null=True)),
                ('timezone', timezone_field.fields.TimeZoneField(default='America/New_York')),
                ('profile_image', models.ImageField(blank=True, null=True, upload_to=greenbudget.app.user.models.upload_to)),
                ('is_active', models.BooleanField(default=True, help_text="Designates whether this user's account is disabled.", verbose_name='Active')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether this user can login to the admin site.', verbose_name='Staff')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates whether this user is a superuser.', verbose_name='Superuser')),
                ('is_first_time', models.BooleanField(default=True, help_text='Designates whether this user has logged in yet.', verbose_name='First Time Login')),
                ('is_verified', models.BooleanField(default=False, help_text='Designates whether this user has verified their email address.', verbose_name='Verified')),
                ('stripe_id', models.CharField(blank=True, editable=False, max_length=128, null=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
                'ordering': ('-created_at',),
            },
            managers=[
                ('objects', greenbudget.app.user.managers.UserManager()),
            ],
        ),
    ]
