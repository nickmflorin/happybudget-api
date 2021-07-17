from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('actual', '0010_actual_contact'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='actual',
            name='vendor',
        ),
    ]
