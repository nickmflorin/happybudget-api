from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0004_remove_old_related_names'),
    ]

    operations = [
        migrations.CreateModel(
            name='BudgetGroup',
            fields=[
            ],
            options={
                'verbose_name': 'Group',
                'verbose_name_plural': 'Groups',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('group.group',),
        ),
        migrations.CreateModel(
            name='TemplateGroup',
            fields=[
            ],
            options={
                'verbose_name': 'Group',
                'verbose_name_plural': 'Groups',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('group.group',),
        ),
    ]
