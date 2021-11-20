from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0012_default_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='order',
            field=models.CharField(default='n', editable=False, max_length=1024),
            preserve_default=False,
        ),
    ]
