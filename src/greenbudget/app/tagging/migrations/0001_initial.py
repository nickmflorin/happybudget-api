import colorful.fields
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Color',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', colorful.fields.RGBColorField(unique=True, validators=[django.core.validators.RegexValidator('^#(?:[0-9a-fA-F]{3}){1,2}$', message='Enter a valid color hexadecimal code.')])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('content_types', models.ManyToManyField(blank=True, limit_choices_to=models.Q(models.Q(('app_label', 'group'), ('model', 'group')), models.Q(('app_label', 'fringe'), ('model', 'fringe')), _connector='OR'), to='contenttypes.ContentType')),
            ],
            options={
                'verbose_name': 'Color',
                'verbose_name_plural': 'Colors',
                'ordering': ('created_at',),
                'get_latest_by': 'created_at',
            },
        ),
        migrations.AddConstraint(
            model_name='color',
            constraint=models.CheckConstraint(check=models.Q(code__startswith='#'), name='tagging_color_valid_hex_code'),
        ),
    ]
