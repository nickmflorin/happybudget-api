# Generated by Django 3.1.7 on 2021-03-03 18:21

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import greenbudget.app.authentication.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ResetUID',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('token', models.CharField(default=greenbudget.app.authentication.models.time_random_uuid, max_length=1024, unique=True)),
                ('used', models.BooleanField(default=False)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'ResetUID',
                'verbose_name_plural': 'ResetUIDs',
            },
        ),
    ]
