from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('actual', '0005_prepare_for_generic_fk_removal'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='actual',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='actual',
            name='object_id',
        ),
    ]
