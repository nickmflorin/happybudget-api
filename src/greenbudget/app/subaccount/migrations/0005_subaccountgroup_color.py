import colorful.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subaccount', '0004_unique_group_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='subaccountgroup',
            name='color',
            field=colorful.fields.RGBColorField(colors=['#797695', '#ff7165', '#80cbc4', '#ce93d8', '#fed835', '#c87987', '#69f0ae', '#a1887f', '#81d4fa', '#f75776', '#66bb6a', '#58add6'], default='#EFEFEF'),
        ),
    ]
