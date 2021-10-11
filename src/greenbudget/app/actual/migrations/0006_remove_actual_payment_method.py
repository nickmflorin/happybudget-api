from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('actual', '0005_actual_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='actual',
            name='payment_method',
        ),
    ]
