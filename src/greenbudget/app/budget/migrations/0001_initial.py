from django.db import migrations, models
import django.db.models.deletion
import greenbudget.app.budget.models
import greenbudget.app.budgeting.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('user', '0001_initial'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseBudget',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('image', models.ImageField(null=True, upload_to=greenbudget.app.budget.models.upload_to)),
                ('actual', models.FloatField(default=0.0)),
                ('accumulated_value', models.FloatField(default=0.0)),
                ('accumulated_fringe_contribution', models.FloatField(default=0.0)),
                ('accumulated_markup_contribution', models.FloatField(default=0.0)),
                ('is_deleting', models.BooleanField(default=False)),
                ('created_by', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='budgets', to='user.user')),
                ('polymorphic_ctype', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_%(app_label)s.%(class)s_set+', to='contenttypes.contenttype')),
            ],
            options={
                'verbose_name': 'Base Budget',
                'verbose_name_plural': 'Base Budgets',
                'ordering': ('-updated_at',),
                'get_latest_by': 'updated_at',
            },
            bases=(models.Model, greenbudget.app.budgeting.models.BudgetingTreeModelMixin),
        ),
        migrations.CreateModel(
            name='Budget',
            fields=[
                ('basebudget_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='budget.basebudget')),
            ],
            options={
                'verbose_name': 'Budget',
                'verbose_name_plural': 'Budgets',
                'abstract': False,
            },
            bases=('budget.basebudget',),
        ),
    ]
