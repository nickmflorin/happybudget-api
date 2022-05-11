from django.db import migrations, models
import django.db.models.deletion
import happybudget.app.budgeting.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Markup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('identifier', models.CharField(max_length=128, null=True)),
                ('description', models.CharField(max_length=128, null=True)),
                ('unit', models.IntegerField(choices=[(0, 'Percent'), (1, 'Flat')], default=0)),
                ('rate', models.FloatField(null=True)),
                ('object_id', models.PositiveIntegerField(db_index=True)),
                ('content_type', models.ForeignKey(limit_choices_to=models.Q(models.Q(('app_label', 'account'), ('model', 'account')), models.Q(('app_label', 'subaccount'), ('model', 'subaccount')), models.Q(('app_label', 'budget'), ('model', 'basebudget')), _connector='OR'), on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('created_by', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='created_%(class)ss', to='user.user')),
                ('updated_by', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='updated_%(class)ss', to='user.user')),
            ],
            options={
                'verbose_name': 'Markup',
                'verbose_name_plural': 'Markups',
                'ordering': ('created_at',),
                'get_latest_by': 'updated_at',
            },
            bases=(models.Model, happybudget.app.budgeting.models.BudgetingModelMixin),
        ),
    ]
