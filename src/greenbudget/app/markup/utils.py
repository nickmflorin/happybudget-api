from django.db import IntegrityError


def markup_set(child):
    objs = child
    if not hasattr(child, '__iter__'):
        objs = child.markups.only('pk').all()
    return set([m.pk for m in objs])


def two_children_have_same_markups(a, b):
    return markup_set(a) == markup_set(b)


def validate_child_markups(child):
    markups_and_children = order_markups(
        parent=child.parent,
        include_children=True
    )
    # The Markup instances that would appear below the child in a table, based
    # on the table ordering constraints and relationships between a Markup and
    # it's children.
    markups_after_child = get_markups_after_child(child, markups_and_children)

    # The Markup instances that would appear after the child in a table, based
    # on the table ordering constraints and relationships between a Markup and
    # it's children.
    markups_before_child = get_markups_before_child(child, markups_and_children)

    child_markups = [obj.pk for obj in child.markups.only('pk').all()]

    if not two_children_have_same_markups(child, markups_after_child):
        raise IntegrityError(
            "Child {pk} has markups {child_markups}, but should have markups "
            "{table_markups}.  This is most likely an indication of corrupted "
            "data".format(
                pk=child.pk,
                child_markups=child_markups,
                table_markups=[obj.pk for obj in markups_after_child]
            )
        )

    for markup_before_child in markups_before_child:
        if markup_before_child.pk in child_markups:
            raise IntegrityError(
                "Child {pk} has markup {markup_before_child} that appears "
                "before the child in the table markups {table_markups}.  This "
                "is most likely an indication of corrupted data".format(
                    pk=child.pk,
                    markup_before_child=markup_before_child.pk,
                    table_markups=[obj.pk for obj in markups_after_child]
                )
            )


def get_markups_after_child(child, markups_and_children=None):
    from .models import Markup
    markups_and_children = markups_and_children or order_markups(
        parent=child.parent,
        include_children=True
    )
    return [
        obj for obj in markups_and_children[
            markups_and_children.index(child) + 1:]
        if isinstance(obj, Markup)
    ]


def get_markups_before_child(child, markups_and_children=None):
    from .models import Markup
    markups_and_children = markups_and_children or order_markups(
        parent=child.parent,
        include_children=True
    )
    return [
        obj for obj in markups_and_children[0:markups_and_children.index(child)]
        if isinstance(obj, Markup)
    ]


def order_markups(parent=None, children=None, include_children=False):
    """
    Uses the order of the children of the provided parent to determine what the
    order of the :obj:`Markup`(s) would be in a table.

    The ordering of the children models dictates the ordering of all other rows
    in the table, so we need to use the children models as a basis for the
    position of the :obj:`Markup` rows.

    Every child can have potentially more than one :obj:`Markup`, so the
    :obj:`Markup`(s) form a filtration around the children:

    - Child A
    - Child B
    - Markup(children = [A, B])
    - Child C
    - Child D
    - Markup(children = [A, B, C, D])
    """
    if children is None and parent is None:
        raise ValueError("Either the children or parent must be provided.")

    children = children
    if parent is not None:
        children = parent.children.prefetch_related('markups').only('pk').all()

    markups_and_children = []
    for child in children:
        child_markups = child.markups.only('pk').all()
        if child not in markups_and_children:
            if include_children:
                markups_and_children.append(child)
            other_children_with_same_markups = [
                c for c in children
                if c.pk != child.pk and two_children_have_same_markups(
                    c, child_markups)
            ]
            if include_children:
                markups_and_children.extend(other_children_with_same_markups)
            for markup in child.markups.all():
                # If the Markup was previously added, we have to remove it at
                # it's first location and move it down the array towards the
                # bottom of the table - since it is now used in more than 1
                # location.
                if markup in markups_and_children:
                    markups_and_children = [
                        m for m in markups_and_children if m != markup]
                markups_and_children.append(markup)
    return markups_and_children


def get_surrounding_markups(parent, markup):
    """
    Returns the :obj:`Markup`(s) that occur after, and thus "surround", the
    provided :obj:`Markup` based on where the :obj:`Markup`(s) lie relative to
    the children models of the parent.
    """
    ordered_markups = order_markups(parent)
    if len(ordered_markups) == 1 or len(ordered_markups) == 0:
        if len(ordered_markups) == 1:
            assert ordered_markups == [markup]
        return []
    return ordered_markups[ordered_markups.index(markup) + 1:]


def contribution_from_markups(value, markups):
    """
    Calculates the additional value contribution from the application of a
    series of :obj:`Markup`(s) to a calculated value.

    For each :obj:`Markup`, the value is altered either by a nominal value
    or a percent value, the determination of which is controlled by the `unit`
    field on the :obj:`Markup`.
    """
    from .models import Markup

    additional_values = []
    for markup in [
            m for m in markups if m.rate is not None and m.unit is not None]:
        if markup.unit == Markup.UNITS.flat:
            additional_values.append(markup.rate)
        else:
            additional_values.append(markup.rate * value)
    return sum(additional_values)


def markup_value(value, markups):
    """
    Applies a series of :obj:`Markup`(s) to a calculated value.

    For each :obj:`Markup`, the value is altered either by a nominal value
    or a percent value, the determination of which is controlled by the `unit`
    field on the :obj:`Markup`.
    """
    return value + contribution_from_markups(value, markups)
