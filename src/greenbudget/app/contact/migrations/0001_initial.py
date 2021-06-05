from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=30)),
                ('last_name', models.CharField(max_length=30)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('role', models.IntegerField(choices=[(0, 'Producer'), (1, 'Executive Producer'), (2, 'Production Manager'), (3, 'Production Designer'), (4, 'Actor'), (5, 'Director'), (6, 'Medic'), (7, 'Wardrobe'), (8, 'Writer'), (9, 'Client'), (10, 'Other')])),
                ('city', models.CharField(max_length=30)),
                ('country', models.CharField(max_length=30)),
                # The package was uninstalled.
                # ('phone_number', phonenumber_field.modelfields.PhoneNumberField(max_length=128, region=None)),
                ('phone_number', models.BigIntegerField(null=True)),
                ('email', models.EmailField(max_length=254)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contacts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Contact',
                'verbose_name_plural': 'Contacts',
                'ordering': ('created_at',),
                'get_latest_by': 'updated_at',
                'unique_together': {('user', 'email'), ('user', 'phone_number')},
            },
        ),
    ]
