from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0012_remove_user_is_admin'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='first_name',
            field=models.CharField(max_length=150, verbose_name='First Name'),
        ),
    ]
