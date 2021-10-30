from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fringe', '0002_fringe_color'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='fringe',
            options={'get_latest_by': 'updated_at', 'ordering': ('created_at',), 'verbose_name': 'Fringe', 'verbose_name_plural': 'Fringes'},
        ),
    ]
