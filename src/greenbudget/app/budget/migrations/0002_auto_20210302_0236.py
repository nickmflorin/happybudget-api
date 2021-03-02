# Generated by Django 3.1.7 on 2021-03-02 02:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='budget',
            name='name',
            field=models.CharField(default='test', max_length=256),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='budget',
            name='production_type',
            field=models.IntegerField(choices=[(0, 'Film'), (1, 'Episodic'), (2, 'Music Video'), (3, 'Commercial'), (4, 'Documentary'), (5, 'Custom')], default=0),
        ),
    ]
