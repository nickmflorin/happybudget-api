from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'ordering': ('-last_login',), 'verbose_name': 'User', 'verbose_name_plural': 'Users'},
        ),
    ]
