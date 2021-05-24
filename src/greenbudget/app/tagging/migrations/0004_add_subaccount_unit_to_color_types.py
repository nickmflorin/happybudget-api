from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('tagging', '0003_tag'),
    ]

    operations = [
        migrations.AlterField(
            model_name='color',
            name='content_types',
            field=models.ManyToManyField(
                blank=True,
                limit_choices_to=models.Q(
                    models.Q(('app_label', 'group'), ('model', 'group')),
                    models.Q(('app_label', 'fringe'), ('model', 'fringe')),
                    models.Q(
                        ('app_label', 'subaccount'),
                        ('model', 'subaccountunit')
                    ), _connector='OR'
                ),
                to='contenttypes.ContentType'
            ),
        ),
    ]