from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tagging', '0006_set_color_name_not_null'),
    ]

    operations = [
        migrations.AddField(
            model_name='tag',
            name='plural_title',
            field=models.CharField(max_length=32, null=True),
        ),
    ]
