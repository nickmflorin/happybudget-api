from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('actual', '0015_ordering_unique'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actual',
            name='order',
            field=models.CharField(default=None, editable=False, max_length=1024),
        ),
    ]
