from django.db import migrations, models
import django.db.models.deletion
import greenbudget.app.budgeting.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('io', '0001_initial'),
        ('contact', '0001_initial'),
        ('tagging', '__first__'),
        ('budget', '0001_initial'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActualType',
            fields=[
                ('tag_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='tagging.tag')),
            ],
            options={
                'verbose_name': 'Actual Type',
                'verbose_name_plural': 'Actual Types',
                'ordering': ('order',),
                'get_latest_by': 'created_at',
            },
            bases=('tagging.tag',),
        ),
        migrations.CreateModel(
            name='Actual',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('order', models.CharField(default=None, editable=False, max_length=1024)),
                ('name', models.CharField(max_length=128, null=True)),
                ('notes', models.CharField(max_length=256, null=True)),
                ('purchase_order', models.CharField(max_length=128, null=True)),
                ('date', models.DateTimeField(null=True)),
                ('payment_id', models.CharField(max_length=50, null=True)),
                ('value', models.FloatField(null=True)),
                ('object_id', models.PositiveIntegerField(db_index=True, null=True)),
                ('actual_type', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='actual.actualtype')),
                ('attachments', models.ManyToManyField(related_name='actuals', to='io.Attachment')),
                ('budget', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='actuals', to='budget.budget')),
                ('contact', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tagged_actuals', to='contact.contact')),
                ('content_type', models.ForeignKey(limit_choices_to=models.Q(models.Q(('app_label', 'markup'), ('model', 'Markup')), models.Q(('app_label', 'subaccount'), ('model', 'BudgetSubAccount')), _connector='OR'), null=True, on_delete=django.db.models.deletion.SET_NULL, to='contenttypes.contenttype')),
                ('created_by', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='created_%(class)ss', to='user.user')),
                ('updated_by', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='updated_%(class)ss', to='user.user')),
            ],
            options={
                'verbose_name': 'Actual',
                'verbose_name_plural': 'Actual',
                'ordering': ('order',),
                'get_latest_by': 'order',
                'unique_together': {('budget', 'order')},
            },
            bases=(models.Model, greenbudget.app.budgeting.models.BudgetingModelMixin),
        ),
    ]
