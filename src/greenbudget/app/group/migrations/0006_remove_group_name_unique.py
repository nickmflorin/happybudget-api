from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0005_color_new_to_color'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='budgetaccountgroup',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='budgetsubaccountgroup',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='templateaccountgroup',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='templatesubaccountgroup',
            unique_together=set(),
        ),
    ]
