from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0005_alter_meta_options'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='budget',
            name='build_days',
        ),
        migrations.RemoveField(
            model_name='budget',
            name='delivery_date',
        ),
        migrations.RemoveField(
            model_name='budget',
            name='location_days',
        ),
        migrations.RemoveField(
            model_name='budget',
            name='prelight_days',
        ),
        migrations.RemoveField(
            model_name='budget',
            name='production_type',
        ),
        migrations.RemoveField(
            model_name='budget',
            name='project_number',
        ),
        migrations.RemoveField(
            model_name='budget',
            name='shoot_date',
        ),
        migrations.RemoveField(
            model_name='budget',
            name='studio_shoot_days',
        ),
    ]
