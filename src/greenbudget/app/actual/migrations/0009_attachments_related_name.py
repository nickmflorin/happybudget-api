from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('io', '0001_initial'),
        ('actual', '0008_actual_name_and_notes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actual',
            name='attachments',
            field=models.ManyToManyField(related_name='actuals', to='io.Attachment'),
        ),
    ]
