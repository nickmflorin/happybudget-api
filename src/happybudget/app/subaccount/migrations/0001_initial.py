from django.db import migrations, models
import django.db.models.deletion
import happybudget.app.budgeting.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('io', '0001_initial'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('contact', '0001_initial'),
        ('user', '0001_initial'),
        ('tagging', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='SubAccount',
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
                ('quantity', models.FloatField(blank=True, null=True)),
                ('rate', models.FloatField(blank=True, null=True)),
                ('multiplier', models.IntegerField(blank=True, null=True)),
                ('fringe_contribution', models.FloatField(default=0.0)),
                ('is_deleting', models.BooleanField(default=False)),
                ('object_id', models.PositiveIntegerField(db_index=True)),
                ('content_type', models.ForeignKey(limit_choices_to=models.Q(models.Q(('app_label', 'account'), ('model', 'Account')), models.Q(('app_label', 'subaccount'), ('model', 'SubAccount')), _connector='OR'), on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('created_by', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='created_%(class)ss', to='user.user')),
                ('polymorphic_ctype', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_%(app_label)s.%(class)s_set+', to='contenttypes.contenttype')),
            ],
            options={
                'verbose_name': 'Sub Account',
                'verbose_name_plural': 'Sub Accounts',
                'ordering': ('order',),
                'get_latest_by': 'order',
            },
            bases=(models.Model, happybudget.app.budgeting.models.BudgetingTreeModelMixin),
        ),
        migrations.CreateModel(
            name='SubAccountUnit',
            fields=[
                ('tag_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='tagging.tag')),
            ],
            options={
                'verbose_name': 'Sub Account Unit',
                'verbose_name_plural': 'Sub Account Units',
                'ordering': ('order',),
                'get_latest_by': 'created_at',
            },
            bases=('tagging.tag',),
        ),
        migrations.CreateModel(
            name='TemplateSubAccount',
            fields=[
                ('subaccount_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='subaccount.subaccount')),
            ],
            options={
                'verbose_name': 'Template Sub Account',
                'verbose_name_plural': 'Template Sub Accounts',
                'abstract': False,
            },
            bases=('subaccount.subaccount',),
        ),
        migrations.AddField(
            model_name='subaccount',
            name='unit',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='subaccount.subaccountunit'),
        ),
        migrations.AddField(
            model_name='subaccount',
            name='updated_by',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='updated_%(class)ss', to='user.user'),
        ),
        migrations.AlterUniqueTogether(
            name='subaccount',
            unique_together={('content_type', 'object_id', 'order')},
        ),
        migrations.CreateModel(
            name='BudgetSubAccount',
            fields=[
                ('subaccount_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='subaccount.subaccount')),
                ('attachments', models.ManyToManyField(related_name='subaccounts', to='io.Attachment')),
                ('contact', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_subaccounts', to='contact.contact')),
            ],
            options={
                'verbose_name': 'Budget Sub Account',
                'verbose_name_plural': 'Budget Sub Accounts',
                'abstract': False,
            },
            bases=('subaccount.subaccount',),
        ),
    ]
