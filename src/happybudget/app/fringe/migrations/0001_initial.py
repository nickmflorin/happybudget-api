from django.db import migrations, models
import happybudget.app.budgeting.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Fringe',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('order', models.CharField(default=None, editable=False, max_length=1024)),
                ('name', models.CharField(max_length=128, null=True)),
                ('description', models.CharField(max_length=128, null=True)),
                ('cutoff', models.FloatField(null=True)),
                ('rate', models.FloatField(null=True)),
                ('unit', models.IntegerField(choices=[(0, 'Percent'), (1, 'Flat')], default=0, null=True)),
            ],
            options={
                'verbose_name': 'Fringe',
                'verbose_name_plural': 'Fringes',
                'ordering': ('order',),
                'get_latest_by': 'order',
            },
            bases=(models.Model, happybudget.app.budgeting.models.BudgetingModelMixin),
        ),
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
