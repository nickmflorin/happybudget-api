from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('budget_item', '0002_budget_item_group'),
        ('budget', '0001_initial'),
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccountGroup',
            fields=[
                ('budgetitemgroup_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='budget_item.budgetitemgroup')),
                ('name', models.CharField(max_length=128)),
                ('budget', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='groups', to='budget.budget')),
            ],
            options={
                'verbose_name': 'Account Group',
                'verbose_name_plural': 'Account Groups',
                'ordering': ('created_at',),
                'get_latest_by': 'created_at',
                'unique_together': {('budget', 'name')},
            },
            bases=('budget_item.budgetitemgroup',),
        ),
    ]
