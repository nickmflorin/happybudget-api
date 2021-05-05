from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0006_remove_group_name_unique'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='new_name',
            field=models.CharField(default='', max_length=128),
            preserve_default=False,
        ),
    ]
