from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0003_fringe'),
        ('subaccount', '0007_extend_subaccount_group_polymorphically'),
    ]

    operations = [
        migrations.AddField(
            model_name='subaccount',
            name='fringes',
            field=models.ManyToManyField(to='budget.Fringe'),
        ),
    ]
