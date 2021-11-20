from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('budget', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contact', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Actual',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('description', models.CharField(max_length=128, null=True)),
                ('purchase_order', models.CharField(max_length=128, null=True)),
                ('date', models.DateTimeField(null=True)),
                ('payment_id', models.CharField(max_length=50, null=True)),
                ('value', models.FloatField(null=True)),
                ('payment_method', models.IntegerField(choices=[(0, 'Check'), (1, 'Card'), (2, 'Wire')], null=True)),
                ('budget', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='actuals', to='budget.budget')),
                ('contact', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_actuals', to='contact.contact')),
                ('created_by', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='created_actuals', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='updated_actuals', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Actual',
                'verbose_name_plural': 'Actual',
                'ordering': ('created_at',),
                'get_latest_by': 'updated_at',
            },
        ),
    ]
