from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0008_group_name_to_polymorphic_base'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='budgetaccountgroup',
            name='name',
        ),
        migrations.RemoveField(
            model_name='budgetsubaccountgroup',
            name='name',
        ),
        migrations.RemoveField(
            model_name='templateaccountgroup',
            name='name',
        ),
        migrations.RemoveField(
            model_name='templatesubaccountgroup',
            name='name',
        ),
    ]
