from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import greenbudget.app.contact.models


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
                ('first_name', models.CharField(max_length=30, null=True)),
                ('last_name', models.CharField(max_length=30, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('type', models.IntegerField(choices=[(0, 'Contractor'), (1, 'Employee'), (2, 'Vendor')], null=True)),
                ('position', models.CharField(max_length=128, null=True)),
                ('company', models.CharField(max_length=128, null=True)),
                ('city', models.CharField(max_length=30, null=True)),
                ('phone_number', models.BigIntegerField(null=True)),
                ('email', models.EmailField(max_length=254, null=True)),
                ('rate', models.IntegerField(null=True)),
                ('image', models.ImageField(null=True, upload_to=greenbudget.app.contact.models.upload_to)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contacts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Contact',
                'verbose_name_plural': 'Contacts',
                'ordering': ('created_at',),
                'get_latest_by': 'updated_at',
            },
        ),
    ]
