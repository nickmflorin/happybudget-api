from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('object_id', models.PositiveIntegerField(db_index=True)),
                ('content_type', models.ForeignKey(limit_choices_to=models.Q(models.Q(('app_label', 'account'), ('model', 'budgetaccount')), models.Q(('app_label', 'subaccount'), ('model', 'budgetsubaccount')), _connector='OR'), on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('polymorphic_ctype', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_history.event_set+', to='contenttypes.contenttype')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Event',
                'verbose_name_plural': 'Events',
                'ordering': ('-created_at',),
                'get_latest_by': 'created_at',
                'base_manager_name': 'non_polymorphic',
            },
            managers=[
                ('objects', django.db.models.manager.Manager()),
                ('non_polymorphic', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='CreateEvent',
            fields=[
                ('event_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='history.event')),
            ],
            options={
                'verbose_name': 'Create Event',
                'verbose_name_plural': 'Create Events',
                'ordering': ('-created_at',),
                'get_latest_by': 'created_at',
            },
            bases=('history.event',),
            managers=[
                ('objects', django.db.models.manager.Manager()),
                ('non_polymorphic', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='FieldAlterationEvent',
            fields=[
                ('event_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='history.event')),
                ('serialized_old_value', models.TextField()),
                ('serialized_new_value', models.TextField()),
                ('field', models.CharField(max_length=256)),
            ],
            options={
                'verbose_name': 'Field Alteration Event',
                'verbose_name_plural': 'Field Alteration Events',
                'ordering': ('-created_at',),
                'get_latest_by': 'created_at',
            },
            bases=('history.event',),
            managers=[
                ('objects', django.db.models.manager.Manager()),
                ('non_polymorphic', django.db.models.manager.Manager()),
            ],
        ),
    ]
