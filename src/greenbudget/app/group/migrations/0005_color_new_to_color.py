from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0004_remove_group_color'),
    ]

    operations = [
        migrations.RenameField(
            model_name='group',
            old_name='color_new',
            new_name='color',
        ),
    ]
