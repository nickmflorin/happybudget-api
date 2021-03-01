# Generated by Django 3.1.7 on 2021-03-01 01:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='BudgetItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('description', models.CharField(max_length=128, null=True)),
                ('object_id', models.PositiveIntegerField()),
                ('estimated', models.DecimalField(decimal_places=2, default=0, max_digits=21)),
                ('content_type', models.ForeignKey(limit_choices_to=models.Q(models.Q(('app_label', 'budget'), ('model', 'Budget')), models.Q(('app_label', 'budget_item'), ('model', 'BudgetItem')), _connector='OR'), on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('polymorphic_ctype', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_budget_item.budgetitem_set+', to='contenttypes.contenttype')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
        ),
        migrations.CreateModel(
            name='GenericBudgetItem',
            fields=[
                ('budgetitem_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='budget_item.budgetitem')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('budget_item.budgetitem',),
        ),
        migrations.CreateModel(
            name='QuantityBudgetItem',
            fields=[
                ('budgetitem_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='budget_item.budgetitem')),
                ('name', models.CharField(default=None, max_length=30, null=True)),
                ('quantity', models.DecimalField(decimal_places=2, default=None, max_digits=10, null=True)),
                ('unit', models.CharField(default=None, max_length=20, null=True)),
                ('rate', models.DecimalField(decimal_places=2, default=None, max_digits=10, null=True)),
                ('fringes', models.DecimalField(decimal_places=1, default=None, max_digits=5, null=True)),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('budget_item.budgetitem',),
        ),
    ]
