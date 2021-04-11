from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contact', '0002_ensure_email_phone_unique'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='contact',
            unique_together={('user', 'email'), ('user', 'phone_number')},
        ),
    ]
