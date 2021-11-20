from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0004_contact_attachments'),
    ]

    operations = [
        migrations.RenameField(
            model_name='contact',
            old_name='user',
            new_name='created_by',
        ),
    ]
