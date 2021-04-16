# Generated by Django 3.1.7 on 2021-04-15 22:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subaccount', '0008_subaccount_fringes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subaccount',
            name='unit',
            field=models.IntegerField(choices=[(0, 'Minutes'), (1, 'Hours'), (2, 'Weeks'), (3, 'Months'), (4, 'Days'), (5, 'Nights'), (6, 'Allow'), (7, 'Flat'), (8, 'Feet'), (9, 'Fare'), (10, 'Units')], null=True),
        ),
    ]
