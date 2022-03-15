import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import greenbudget.app.pdf.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='HeaderTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32, validators=[django.core.validators.MinLengthValidator(1)])),
                ('header', models.TextField(null=True)),
                ('left_info', models.TextField(null=True)),
                ('right_info', models.TextField(null=True)),
                ('left_image', models.ImageField(null=True, upload_to=greenbudget.app.pdf.models.upload_to)),
                ('right_image', models.ImageField(null=True, upload_to=greenbudget.app.pdf.models.upload_to)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='header_templates', to='user.user')),
            ],
            options={
                'verbose_name': 'Header Template',
                'verbose_name_plural': 'Header Templates',
                'unique_together': {('created_by', 'name')},
            },
        ),
    ]
