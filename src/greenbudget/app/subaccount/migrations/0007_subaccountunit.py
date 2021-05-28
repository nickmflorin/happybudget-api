from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tagging', '0004_add_subaccount_unit_to_color_types'),
        ('subaccount', '0006_added_additional_tags'),
    ]

    operations = [
        migrations.CreateModel(
            name='SubAccountUnit',
            fields=[
                ('tag_ptr', models.OneToOneField(
                    auto_created=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    parent_link=True,
                    primary_key=True,
                    serialize=False,
                    to='tagging.tag'
                )),
                ('color', models.ForeignKey(
                    limit_choices_to=models.Q(
                        ('content_types__app_label', 'subaccount'),
                        ('content_types__model', 'subaccountunit')
                    ),
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='tagging.color'
                )),
            ],
            options={
                'verbose_name': 'Sub Account Unit',
                'verbose_name_plural': 'Sub Account Units',
                'ordering': ('order',),
                'get_latest_by': 'created_at',
            },
            bases=('tagging.tag',),
        ),
    ]
