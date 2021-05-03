from django.db import migrations

def map_group_colors(apps, schema_editor):
    Group = apps.get_model('group', 'Group')
    Color = apps.get_model('tagging', 'Color')

    for group in Group.objects.all():
        if group.color is None:
            continue
        try:
            color_obj = Color.objects.get(code=group.color)
        except Color.DoesNotExist:
            color_obj = Color.objects.create(code=group.color)
        color_obj.content_types.add(Group)


class Migration(migrations.Migration):
    dependencies = [
        ('group', '0002_group_color_new'),
    ]

    operations = [
        migrations.RunPython(map_group_colors),
    ]