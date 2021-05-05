from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0009_remove_polymorphic_extension_name'),
    ]

    operations = [
        migrations.RenameField(
            model_name='group',
            old_name='new_name',
            new_name='name',
        ),
    ]
