from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0007_add_type_position'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contact',
            name='role',
        ),
    ]
