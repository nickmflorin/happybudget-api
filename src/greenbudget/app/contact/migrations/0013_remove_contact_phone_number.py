from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0012_migrate_contact_phone_number'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contact',
            name='phone_number',
        ),
    ]
