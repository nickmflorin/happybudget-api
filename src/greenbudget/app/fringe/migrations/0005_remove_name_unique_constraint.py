from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fringe', '0004_allow_name_null'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='fringe',
            unique_together=set(),
        ),
    ]
