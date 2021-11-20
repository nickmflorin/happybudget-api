from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('actual', '0011_default_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actual',
            name='order',
            field=models.CharField(default='n', editable=False, max_length=1024),
            preserve_default=False,
        ),
    ]
