from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0004_basebudget_image'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='basebudget',
            unique_together=set(),
        ),
    ]
