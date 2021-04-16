def fringe_value(value, fringes):
    """
    Applies a series of :obj:`Fringe`(s) to a calculated value.

    For each :obj:`Fringe`, the value is altered either by a nominal value
    or a percent value, the determination of which is controlled by the `unit`
    field on the :obj:`Fringe`.
    """
    from .models import Fringe

    additional_values = []
    for fringe in [f for f in fringes if f.rate is not None]:
        if fringe.unit == Fringe.UNITS.flat:
            additional_values.append(fringe.rate)
        else:
            if fringe.cutoff is None or fringe.cutoff >= value:
                additional_values.append(fringe.rate * value)
            else:
                # In this case, the rate only applies to the value up until
                # the cutoff.
                additional_values.append(fringe.rate * fringe.cutoff)
    return value + sum(additional_values)
