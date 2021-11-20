from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0005_alter_meta_options'),
        ('fringe', '0008_latest_by_order'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='fringe',
            unique_together={('budget', 'order')},
        ),
    ]
