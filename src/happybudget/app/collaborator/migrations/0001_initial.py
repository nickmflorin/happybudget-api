from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('user', '0002_order_by_last_login'),
    ]

    operations = [
        migrations.CreateModel(
            name='Collaborator',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('object_id', models.PositiveIntegerField(db_index=True)),
                ('access_type', models.IntegerField(choices=[(0, 'View Only'), (1, 'Editor'), (2, 'Owner')], default=0)),
                ('content_type', models.ForeignKey(limit_choices_to=models.Q(('app_label', 'budget'), ('model', 'Budget')), on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('user', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='collaborations', to='user.user')),
            ],
            options={
                'verbose_name': 'Collaborator',
                'verbose_name_plural': 'Collaborators',
                'ordering': ('created_at',),
                'get_latest_by': 'created_at',
                'unique_together': {('content_type', 'object_id', 'user')},
            },
        ),
    ]
