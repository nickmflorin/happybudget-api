from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('io', '0001_initial'),
        ('contact', '0003_phone_number_to_string'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='attachments',
            field=models.ManyToManyField(related_name='contacts', to='io.Attachment'),
        ),
    ]
