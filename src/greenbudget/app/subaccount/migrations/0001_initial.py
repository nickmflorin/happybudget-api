from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('fringe', '0001_initial'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('tagging', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contact', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SubAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('identifier', models.CharField(max_length=128, null=True)),
                ('description', models.CharField(max_length=128, null=True)),
                ('quantity', models.IntegerField(null=True)),
                ('rate', models.FloatField(null=True)),
                ('multiplier', models.IntegerField(null=True)),
                ('estimated', models.FloatField(default=0.0)),
                ('object_id', models.PositiveIntegerField(db_index=True)),
                ('content_type', models.ForeignKey(limit_choices_to=models.Q(models.Q(('app_label', 'account'), ('model', 'Account')), models.Q(('app_label', 'subaccount'), ('model', 'SubAccount')), _connector='OR'), on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('created_by', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='created_subaccounts', to=settings.AUTH_USER_MODEL)),
                ('fringes', models.ManyToManyField(to='fringe.Fringe')),
                ('polymorphic_ctype', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_subaccount.subaccount_set+', to='contenttypes.contenttype')),
            ],
            options={
                'verbose_name': 'Sub Account',
                'verbose_name_plural': 'Sub Accounts',
                'ordering': ('created_at',),
                'get_latest_by': 'updated_at',
            },
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
                'base_manager_name': 'objects',
            },
            bases=('subaccount.subaccount',),
        ),
        migrations.CreateModel(
            name='SubAccountUnit',
            fields=[
                ('tag_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='tagging.tag')),
                ('color', models.ForeignKey(blank=True, limit_choices_to=models.Q(('content_types__app_label', 'subaccount'), ('content_types__model', 'subaccountunit')), null=True, on_delete=django.db.models.deletion.SET_NULL, to='tagging.color')),
            ],
            options={
                'verbose_name': 'Sub Account Unit',
                'verbose_name_plural': 'Sub Account Units',
                'ordering': ('order',),
                'get_latest_by': 'created_at',
            },
            bases=('tagging.tag',),
        ),
        migrations.AddField(
            model_name='subaccount',
            name='unit',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='subaccount.subaccountunit'),
        ),
        migrations.AddField(
            model_name='subaccount',
            name='updated_by',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='updated_subaccounts', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='BudgetSubAccount',
            fields=[
                ('subaccount_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='subaccount.subaccount')),
                ('actual', models.FloatField(default=0.0)),
                ('contact', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_subaccounts', to='contact.contact')),
            ],
            options={
                'verbose_name': 'Budget Sub Account',
                'verbose_name_plural': 'Budget Sub Accounts',
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('subaccount.subaccount',),
        ),
    ]
