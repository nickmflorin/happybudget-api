from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('account', '0014_rename_new_parent_created_by_updated_by'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('subaccount', '0024_rename_new_parent_created_by_updated_by'),
        ('budget', '0009_created_by_non_null'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Markup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('identifier', models.CharField(max_length=128, null=True)),
                ('description', models.CharField(max_length=128, null=True)),
                ('unit', models.IntegerField(choices=[(0, 'Percent'), (1, 'Flat')], default=0)),
                ('rate', models.FloatField(null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='created_markups', to=settings.AUTH_USER_MODEL)),
                ('polymorphic_ctype', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_markup.markup_set+', to='contenttypes.contenttype')),
                ('updated_by', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='updated_markups', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Markup',
                'verbose_name_plural': 'Markups',
                'ordering': ('-created_at',),
                'get_latest_by': 'updated_at',
            },
        ),
        migrations.CreateModel(
            name='BudgetSubAccountMarkup',
            fields=[
                ('markup_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='markup.markup')),
                ('object_id', models.PositiveIntegerField(db_index=True)),
                ('children', models.ManyToManyField(related_name='markups', to='subaccount.BudgetSubAccount')),
                ('content_type', models.ForeignKey(limit_choices_to=models.Q(models.Q(('app_label', 'account'), ('model', 'budgetaccount')), models.Q(('app_label', 'subaccount'), ('model', 'budgetsubaccount')), _connector='OR'), on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
            ],
            options={
                'verbose_name': 'Sub Account Markup',
                'verbose_name_plural': 'Sub Account Markups',
                'ordering': ('-created_at',),
                'get_latest_by': 'updated_at',
            },
            bases=('markup.markup',),
        ),
        migrations.CreateModel(
            name='BudgetAccountMarkup',
            fields=[
                ('markup_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='markup.markup')),
                ('children', models.ManyToManyField(related_name='markups', to='account.BudgetAccount')),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='markups', to='budget.budget')),
            ],
            options={
                'verbose_name': 'Account Markup',
                'verbose_name_plural': 'Account Markups',
                'ordering': ('-created_at',),
                'get_latest_by': 'updated_at',
            },
            bases=('markup.markup',),
        ),
    ]
