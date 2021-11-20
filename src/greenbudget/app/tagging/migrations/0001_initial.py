import colorful.fields
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


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
                ('name', models.CharField(max_length=32, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Color',
                'verbose_name_plural': 'Colors',
                'ordering': ('created_at',),
                'get_latest_by': 'created_at',
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=32)),
                ('plural_title', models.CharField(blank=True, max_length=32, null=True)),
                ('order', models.IntegerField(null=True)),
                ('polymorphic_ctype', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_tagging.tag_set+', to='contenttypes.contenttype')),
            ],
            options={
                'verbose_name': 'Tag',
                'verbose_name_plural': 'All Tags',
                'ordering': ('created_at',),
                'get_latest_by': 'created_at',
            },
        ),
        migrations.AddConstraint(
            model_name='color',
            constraint=models.CheckConstraint(check=models.Q(code__startswith='#'), name='tagging_color_valid_hex_code'),
        ),
        migrations.AlterUniqueTogether(
            name='tag',
            unique_together={('title', 'polymorphic_ctype_id')},
        ),
    ]
