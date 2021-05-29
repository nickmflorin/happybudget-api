from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tagging', '0005_default_color_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='color',
            name='name',
            # Unnamed will never be used, because we set all the names to non-null
            # values in the previous migration.
            field=models.CharField(default='Unnamed', max_length=32, unique=True),
            preserve_default=False,
        ),
    ]
