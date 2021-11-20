from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import greenbudget.app.budget.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseBudget',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('estimated', models.FloatField(default=0.0)),
                ('image', models.ImageField(null=True, upload_to=greenbudget.app.budget.models.upload_to)),
                ('created_by', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='budgets', to=settings.AUTH_USER_MODEL)),
                ('polymorphic_ctype', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_budget.basebudget_set+', to='contenttypes.contenttype')),
            ],
            options={
                'verbose_name': 'Base Budget',
                'verbose_name_plural': 'Base Budgets',
                'ordering': ('-updated_at',),
                'get_latest_by': 'updated_at',
            },
        ),
        migrations.CreateModel(
            name='Budget',
            fields=[
                ('basebudget_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='budget.basebudget')),
                ('project_number', models.IntegerField(default=0)),
                ('production_type', models.IntegerField(choices=[(0, 'Film'), (1, 'Episodic'), (2, 'Music Video'), (3, 'Commercial'), (4, 'Documentary'), (5, 'Custom')], default=0)),
                ('shoot_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('delivery_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('build_days', models.IntegerField(default=0)),
                ('prelight_days', models.IntegerField(default=0)),
                ('studio_shoot_days', models.IntegerField(default=0)),
                ('location_days', models.IntegerField(default=0)),
                ('actual', models.FloatField(default=0.0)),
            ],
            options={
                'verbose_name': 'Budget',
                'verbose_name_plural': 'Budgets',
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('budget.basebudget',),
        ),
    ]
