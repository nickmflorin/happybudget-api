# Generated by Django 3.1.7 on 2021-03-02 03:25

from django.db import migrations
import timezone_field.fields


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_auto_20210301_0105'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='timezone',
            field=timezone_field.fields.TimeZoneField(default='America/New_York'),
        ),
    ]