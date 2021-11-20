from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0014_order_by_order'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='contact',
            options={'get_latest_by': 'order', 'ordering': ('order',), 'verbose_name': 'Contact', 'verbose_name_plural': 'Contacts'},
        ),
    ]
