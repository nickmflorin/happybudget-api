from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0011_polymorphic_manager_fix'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='budgetaccountgroup',
            options={'base_manager_name': 'objects', 'verbose_name': 'Account Group', 'verbose_name_plural': 'Account Groups'},
        ),
        migrations.AlterModelOptions(
            name='budgetsubaccountgroup',
            options={'base_manager_name': 'objects', 'verbose_name': 'Sub Account Group', 'verbose_name_plural': 'Sub Account Groups'},
        ),
        migrations.AlterModelOptions(
            name='templateaccountgroup',
            options={'base_manager_name': 'objects', 'verbose_name': 'Account Group', 'verbose_name_plural': 'Account Groups'},
        ),
        migrations.AlterModelOptions(
            name='templatesubaccountgroup',
            options={'base_manager_name': 'objects', 'verbose_name': 'Sub Account Group', 'verbose_name_plural': 'Sub Account Groups'},
        ),
    ]
