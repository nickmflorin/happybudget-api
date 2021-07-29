from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import greenbudget.app.pdf.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Block',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
        ),
        migrations.CreateModel(
            name='ExportField',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'verbose_name': 'Export Field',
                'verbose_name_plural': 'Export Fields',
            },
        ),
        migrations.CreateModel(
            name='TextDataElement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.PositiveIntegerField(db_index=True)),
                ('content_type', models.ForeignKey(limit_choices_to=models.Q(models.Q(('app_label', 'pdf'), ('model', 'TextGroup')), models.Q(('app_label', 'pdf'), ('model', 'Block')), _connector='OR'), on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('polymorphic_ctype', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_pdf.textdataelement_set+', to='contenttypes.contenttype')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
        ),
        migrations.CreateModel(
            name='HeadingBlock',
            fields=[
                ('block_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='pdf.block')),
                ('level', models.IntegerField(default=2, validators=[django.core.validators.MaxValueValidator(6), django.core.validators.MinValueValidator(1)])),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('pdf.block',),
        ),
        migrations.CreateModel(
            name='ParagraphBlock',
            fields=[
                ('block_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='pdf.block')),
            ],
            options={
                'verbose_name': 'Export Field',
                'verbose_name_plural': 'Export Fields',
            },
            bases=('pdf.block',),
        ),
        migrations.CreateModel(
            name='TextFragment',
            fields=[
                ('textdataelement_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='pdf.textdataelement')),
                ('text', models.CharField(max_length=256)),
                ('is_bold', models.BooleanField(default=False)),
                ('is_italic', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Text Fragment',
                'verbose_name_plural': 'Text Fragments',
            },
            bases=('pdf.textdataelement',),
        ),
        migrations.CreateModel(
            name='TextFragmentGroup',
            fields=[
                ('textdataelement_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='pdf.textdataelement')),
            ],
            options={
                'verbose_name': 'Text Group',
                'verbose_name_plural': 'Text Groups',
            },
            bases=('pdf.textdataelement',),
        ),
        migrations.AddField(
            model_name='block',
            name='field',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blocks', to='pdf.exportfield'),
        ),
        migrations.AddField(
            model_name='block',
            name='polymorphic_ctype',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_pdf.block_set+', to='contenttypes.contenttype'),
        ),
        migrations.CreateModel(
            name='HeaderTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32, validators=[django.core.validators.MinLengthValidator(1)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('left_image', models.ImageField(null=True, upload_to=greenbudget.app.pdf.models.upload_to)),
                ('right_image', models.ImageField(null=True, upload_to=greenbudget.app.pdf.models.upload_to)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='header_templates', to=settings.AUTH_USER_MODEL)),
                ('header', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='header_template_header', to='pdf.exportfield')),
                ('left_info', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='header_template_left_info', to='pdf.exportfield')),
                ('right_info', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='header_template_right_info', to='pdf.exportfield')),
            ],
            options={
                'verbose_name': 'Header Template',
                'verbose_name_plural': 'Header Templates',
                'unique_together': {('created_by', 'name')},
            },
        ),
    ]
