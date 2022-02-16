from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('user', '0013_alter_user_first_name'),
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PublicToken',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('public_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('private_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('expires_at', models.DateTimeField(null=True)),
                ('object_id', models.PositiveIntegerField(db_index=True)),
                ('content_type', models.ForeignKey(limit_choices_to=models.Q(models.Q(('app_label', 'account'), ('model', 'Account')), models.Q(('app_label', 'subaccount'), ('model', 'SubAccount')), _connector='OR'), on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('created_by', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='created_%(class)ss', to='user.user')),
            ],
            options={
                'verbose_name': 'Public Token',
                'verbose_name_plural': 'Public Tokens',
                'ordering': ('created_at',),
                'get_latest_by': 'created_at',
                'unique_together': {('content_type', 'object_id')},
            },
        ),
    ]
