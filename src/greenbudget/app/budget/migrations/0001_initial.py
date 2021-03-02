# Generated by Django 3.1.7 on 2021-03-01 01:07

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Budget',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('project_number', models.IntegerField(default=0)),
                ('production_type', models.IntegerField(choices=[(0, 'Film'), (1, 'Episodic'), (2, 'Episodic'), (3, 'Commercial'), (4, 'Documentary'), (5, 'Custom')], default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('shoot_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('delivery_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('build_days', models.IntegerField(default=0)),
                ('prelight_days', models.IntegerField(default=0)),
                ('studio_shoot_days', models.IntegerField(default=0)),
                ('location_days', models.IntegerField(default=0)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='budgets', to=settings.AUTH_USER_MODEL)),
                ('polymorphic_ctype', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_budget.budget_set+', to='contenttypes.contenttype')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
        ),
    ]