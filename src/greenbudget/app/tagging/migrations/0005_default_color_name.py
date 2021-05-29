from django.db import migrations


def get_first_color_with_name(model_cls, color, name):
    while True:
        instance = model_cls.objects.filter(name=name).first()
        if instance != color:
            return instance



def get_unique_name(model_cls, color, base="Unnamed"):
    index = 0
    while True:
        name = base
        if index != 0:
            name = "%s(%s)" % (base, index)
        instance = get_first_color_with_name(model_cls, color, name)
        if instance is None:
            return name
        index += 1


def forwards_func(apps, schema_editor):
    Color = apps.get_model("tagging", "Color")

    for color in Color.objects.all():
        if color.name is None:
            color.name = get_unique_name(Color, color)
            color.save()


class Migration(migrations.Migration):

    dependencies = [
        ('tagging', '0004_add_subaccount_unit_to_color_types'),
    ]

    operations = [
        migrations.RunPython(forwards_func)
    ]