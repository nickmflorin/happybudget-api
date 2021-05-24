from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('tagging', '0002_color_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=32)),
                ('order', models.IntegerField(null=True)),
                ('polymorphic_ctype', models.ForeignKey(
                    editable=False,
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='polymorphic_tagging.tag_set+',
                    to='contenttypes.contenttype'
                )),
            ],
            options={
                'verbose_name': 'Tag',
                'verbose_name_plural': 'Tags',
                'ordering': ('created_at',),
                'get_latest_by': 'created_at',
                'unique_together': {('title', 'polymorphic_ctype_id')},
            },
        ),
    ]
