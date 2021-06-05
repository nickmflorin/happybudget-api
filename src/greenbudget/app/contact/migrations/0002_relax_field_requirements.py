from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='city',
            field=models.CharField(max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='contact',
            name='country',
            field=models.CharField(max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='contact',
            name='email',
            field=models.EmailField(max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name='contact',
            name='last_name',
            field=models.CharField(max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='contact',
            name='phone_number',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='contact',
            name='role',
            field=models.IntegerField(choices=[(0, 'Producer'), (1, 'Executive Producer'), (2, 'Production Manager'), (3, 'Production Designer'), (4, 'Actor'), (5, 'Director'), (6, 'Medic'), (7, 'Wardrobe'), (8, 'Writer'), (9, 'Client'), (10, 'Other')], null=True),
        ),
    ]
