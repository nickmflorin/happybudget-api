from django.db import migrations

from greenbudget.app.tabling.utils import lexographic_midpoint


def forwards_func(apps, schema_editor):
    Fringe = apps.get_model("fringe", "Fringe")
    db_alias = schema_editor.connection.alias

    fk_pivots = ('budget_id', )
    model_cls = Fringe

    # Logic is directly copied from model manager because we do not have access
    # to manager methods inside of migrations.
    def reorder(fk_filter):
        instances = model_cls.objects.filter(**fk_filter).all()
        if len(instances) != 0:
            # Start the first instance off at the midpoint of the alphabet.
            instances[0].order = lexographic_midpoint()
            if len(instances) != 1:
                # Start the second instance off at the midpoint between the
                # first instance and the end of the alphabet.
                instances[1].order = lexographic_midpoint(
                    lower=instances[0].order
                )
                # Continue the above logic for the rest of the instances.
                for i, instance in enumerate(instances[2:]):
                    instance.order = lexographic_midpoint(
                        lower=instances[i + 1].order
                    )
        return instances

    def construct_filter(obj):
        pivot_filter = {}
        for fk_pivot in fk_pivots:
            pivot_filter[fk_pivot] = getattr(obj, fk_pivot)
        return pivot_filter

    distinct_filters = [
        construct_filter(obj)
        for obj in model_cls.objects.order_by(*tuple(fk_pivots))
        .distinct(*tuple(fk_pivots))
    ]
    updated = []
    for fk_filter in distinct_filters:
        updated += reorder(fk_filter)

    model_cls.objects.using(db_alias).bulk_update(updated, ["order"])


class Migration(migrations.Migration):

    dependencies = [
        ('fringe', '0004_fringe_order'),
    ]

    operations = [
        migrations.RunPython(forwards_func),
    ]
