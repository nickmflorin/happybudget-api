from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0013_order_non_null'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='contact',
            options={'get_latest_by': 'updated_at', 'ordering': ('order',), 'verbose_name': 'Contact', 'verbose_name_plural': 'Contacts'},
        ),
    ]
