# Generated by Django 3.1.7 on 2021-06-02 22:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0003_identifier_nullable'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='budgetaccount',
            options={'base_manager_name': 'objects', 'verbose_name': 'Account', 'verbose_name_plural': 'Accounts'},
        ),
        migrations.AlterModelOptions(
            name='templateaccount',
            options={'base_manager_name': 'objects', 'verbose_name': 'Account', 'verbose_name_plural': 'Accounts'},
        ),
    ]