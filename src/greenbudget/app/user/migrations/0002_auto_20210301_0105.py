# Generated by Django 3.1.7 on 2021-03-01 01:05

from django.db import migrations
import greenbudget.app.user.managers


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='user',
            managers=[
                ('objects', greenbudget.app.user.managers.UserManager()),
            ],
        ),
    ]
