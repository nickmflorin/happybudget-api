from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tagging', '0007_tag_plural_title'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='tag',
            options={'get_latest_by': 'created_at', 'ordering': ('created_at',), 'verbose_name': 'Tag', 'verbose_name_plural': 'All Tags'},
        ),
        migrations.AlterField(
            model_name='tag',
            name='plural_title',
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
    ]
