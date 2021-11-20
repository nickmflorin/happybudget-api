from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0005_alter_meta_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='order',
            field=models.CharField(default='', max_length=1024, null=True),
        ),
    ]
