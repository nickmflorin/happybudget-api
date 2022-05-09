def contribution_from_markups(value, markups):
    """
    Calculates the additional value contribution from the application of a
    series of :obj:`Markup`(s) to a calculated value.

    For each :obj:`Markup`, the value is altered either by a nominal value
    or a percent value, the determination of which is controlled by the `unit`
    field on the :obj:`Markup`.
    """
    # pylint: disable=import-outside-toplevel
    from .models import Markup

    additional_values = []
    for markup in [
            m for m in markups if m.rate is not None
            and m.unit == Markup.UNITS.percent]:
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
