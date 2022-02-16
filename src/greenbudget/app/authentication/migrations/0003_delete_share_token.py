from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0002_create_public_token'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ShareToken',
        ),
    ]
