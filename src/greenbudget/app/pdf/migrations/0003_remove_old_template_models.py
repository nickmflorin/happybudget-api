from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pdf', '0002_change_tempate_fields_to_rich_text'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='headingblock',
            name='block_ptr',
        ),
        migrations.RemoveField(
            model_name='paragraphblock',
            name='block_ptr',
        ),
        migrations.RemoveField(
            model_name='textdataelement',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='textdataelement',
            name='polymorphic_ctype',
        ),
        migrations.RemoveField(
            model_name='textfragment',
            name='textdataelement_ptr',
        ),
        migrations.RemoveField(
            model_name='textfragmentgroup',
            name='textdataelement_ptr',
        ),
        migrations.DeleteModel(
            name='Block',
        ),
        migrations.DeleteModel(
            name='ExportField',
        ),
        migrations.DeleteModel(
            name='HeadingBlock',
        ),
        migrations.DeleteModel(
            name='ParagraphBlock',
        ),
        migrations.DeleteModel(
            name='TextDataElement',
        ),
        migrations.DeleteModel(
            name='TextFragment',
        ),
        migrations.DeleteModel(
            name='TextFragmentGroup',
        ),
    ]
