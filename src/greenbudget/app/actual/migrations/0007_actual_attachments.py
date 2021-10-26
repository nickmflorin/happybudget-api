from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('io', '0001_initial'),
        ('actual', '0006_remove_actual_payment_method'),
    ]

    operations = [
        migrations.AddField(
            model_name='actual',
            name='attachments',
            field=models.ManyToManyField(to='io.Attachment'),
        ),
    ]
