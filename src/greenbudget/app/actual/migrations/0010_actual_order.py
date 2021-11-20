from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('actual', '0009_attachments_related_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='actual',
            name='order',
            field=models.CharField(default='', max_length=1024, null=True),
        ),
    ]
