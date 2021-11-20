from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0010_updated_by_created_by_non_editable'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='order',
            field=models.CharField(default='', max_length=1024, null=True),
        ),
    ]
