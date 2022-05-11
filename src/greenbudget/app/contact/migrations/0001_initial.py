from django.db import migrations, models
import django.db.models.deletion
import happybudget.app.contact.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('io', '0001_initial'),
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('order', models.CharField(default=None, editable=False, max_length=1024)),
                ('first_name', models.CharField(max_length=30, null=True)),
                ('last_name', models.CharField(max_length=30, null=True)),
                ('contact_type', models.IntegerField(choices=[(0, 'Contractor'), (1, 'Employee'), (2, 'Vendor')], null=True)),
                ('position', models.CharField(max_length=128, null=True)),
                ('company', models.CharField(max_length=128, null=True)),
                ('city', models.CharField(max_length=30, null=True)),
                ('phone_number', models.CharField(max_length=128, null=True)),
                ('email', models.EmailField(max_length=254, null=True)),
                ('rate', models.IntegerField(null=True)),
                ('image', models.ImageField(null=True, upload_to=happybudget.app.contact.models.upload_to)),
                ('notes', models.CharField(max_length=256, null=True)),
                ('attachments', models.ManyToManyField(related_name='contacts', to='io.Attachment')),
                ('created_by', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='created_%(class)ss', to='user.user')),
                ('updated_by', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='updated_%(class)ss', to='user.user')),
            ],
            options={
                'verbose_name': 'Contact',
                'verbose_name_plural': 'Contacts',
                'ordering': ('order',),
                'get_latest_by': 'order',
                'unique_together': {('created_by', 'order')},
            },
        ),
    ]
