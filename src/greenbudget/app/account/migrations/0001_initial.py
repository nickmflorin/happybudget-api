from django.db import migrations, models
import django.db.models.deletion
import happybudget.app.budgeting.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('user', '0001_initial'),
        ('budget', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('order', models.CharField(default=None, editable=False, max_length=1024)),
                ('identifier', models.CharField(blank=True, max_length=128, null=True)),
                ('description', models.CharField(blank=True, max_length=128, null=True)),
                ('actual', models.FloatField(blank=True, default=0.0)),
                ('accumulated_value', models.FloatField(default=0.0)),
                ('accumulated_fringe_contribution', models.FloatField(default=0.0)),
                ('markup_contribution', models.FloatField(default=0.0)),
                ('accumulated_markup_contribution', models.FloatField(default=0.0)),
                ('is_deleting', models.BooleanField(default=False)),
                ('created_by', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='created_%(class)ss', to='user.user')),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='children', to='budget.basebudget')),
                ('polymorphic_ctype', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_%(app_label)s.%(class)s_set+', to='contenttypes.contenttype')),
                ('updated_by', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='updated_%(class)ss', to='user.user')),
            ],
            options={
                'verbose_name': 'Account',
                'verbose_name_plural': 'Accounts',
                'ordering': ('order',),
                'get_latest_by': 'order',
                'unique_together': {('parent', 'order')},
            },
            bases=(models.Model, happybudget.app.budgeting.models.BudgetingTreeModelMixin),
        ),
        migrations.CreateModel(
            name='BudgetAccount',
            fields=[
                ('account_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='account.account')),
            ],
            options={
                'verbose_name': 'Account',
                'verbose_name_plural': 'Accounts',
                'abstract': False,
            },
            bases=('account.account',),
        ),
        migrations.CreateModel(
            name='TemplateAccount',
            fields=[
                ('account_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='account.account')),
            ],
            options={
                'verbose_name': 'Account',
                'verbose_name_plural': 'Accounts',
                'abstract': False,
            },
            bases=('account.account',),
        ),
    ]
