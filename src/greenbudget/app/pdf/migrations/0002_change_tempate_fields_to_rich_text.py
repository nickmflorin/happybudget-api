from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pdf', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='headertemplate',
            name='header',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='headertemplate',
            name='left_info',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='headertemplate',
            name='right_info',
            field=models.TextField(null=True),
        ),
    ]
