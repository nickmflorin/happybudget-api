from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0013_remove_contact_phone_number'),
    ]

    operations = [
        migrations.RenameField(
            model_name='contact',
            old_name='phone_number2',
            new_name='phone_number',
        ),
    ]
