from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('template', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='template',
            options={'verbose_name': 'Template', 'verbose_name_plural': 'Templates'},
        ),
    ]
