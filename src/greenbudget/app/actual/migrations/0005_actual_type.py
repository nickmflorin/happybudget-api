from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tagging', '0002_color_content_types'),
        ('actual', '0004_actual_owner'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActualType',
            fields=[
                ('tag_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='tagging.tag')),
                ('color', models.ForeignKey(blank=True, limit_choices_to=models.Q(('content_types__app_label', 'actual'), ('content_types__model', 'actualtype')), null=True, on_delete=django.db.models.deletion.SET_NULL, to='tagging.color')),
            ],
            options={
                'verbose_name': 'Actual Type',
                'verbose_name_plural': 'Actual Types',
                'ordering': ('order',),
                'get_latest_by': 'created_at',
            },
            bases=('tagging.tag',),
        ),
        migrations.AddField(
            model_name='actual',
            name='actual_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='actual.actualtype'),
        ),
    ]
