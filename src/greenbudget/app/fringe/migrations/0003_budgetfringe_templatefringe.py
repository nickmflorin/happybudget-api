from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fringe', '0002_fringe_color'),
    ]

    operations = [
        migrations.CreateModel(
            name='BudgetFringe',
            fields=[
            ],
            options={
                'verbose_name': 'Fringe',
                'verbose_name_plural': 'Fringes',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('fringe.fringe',),
        ),
        migrations.CreateModel(
            name='TemplateFringe',
            fields=[
            ],
            options={
                'verbose_name': 'Fringe',
                'verbose_name_plural': 'Fringes',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('fringe.fringe',),
        ),
    ]
