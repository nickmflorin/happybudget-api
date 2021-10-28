from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('actual', '0007_actual_attachments'),
    ]

    operations = [
        migrations.RenameField(
            model_name='actual',
            old_name='description',
            new_name='name',
        ),
        migrations.AddField(
            model_name='actual',
            name='notes',
            field=models.CharField(max_length=256, null=True),
        ),
    ]
