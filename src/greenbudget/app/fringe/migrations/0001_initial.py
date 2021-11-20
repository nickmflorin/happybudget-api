from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('budget', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Fringe',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, null=True)),
                ('description', models.CharField(max_length=128, null=True)),
                ('cutoff', models.FloatField(null=True)),
                ('rate', models.FloatField(null=True)),
                ('unit', models.IntegerField(choices=[(0, 'Percent'), (1, 'Flat')], default=0, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('budget', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fringes', to='budget.basebudget')),
                ('created_by', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='created_fringes', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='updated_fringes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Fringe',
                'verbose_name_plural': 'Fringes',
                'ordering': ('-created_at',),
                'get_latest_by': 'updated_at',
            },
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
