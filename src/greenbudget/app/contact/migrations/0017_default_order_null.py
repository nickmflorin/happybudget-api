from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0016_ordering_unique'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='order',
            field=models.CharField(default=None, editable=False, max_length=1024),
        ),
    ]
