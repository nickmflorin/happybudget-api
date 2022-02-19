def cumulative_product(*values):
    if len(values) == 1:
        array = values[0]
        assert hasattr(array, '__iter__'), \
            "The provided value is not an iterable."
    else:
        array = list(values)

    assert len(array) != 0, "At least one value must be provided."
    if any([
        not isinstance(vi, int) and not isinstance(vi, float)
        for vi in array
    ]):
        raise Exception(
            "Encountered non-numeric values.  All values must be numeric.")

    cumulative_product = array[0]
    for v in array[1:]:
        cumulative_product = v * cumulative_product
    return cumulative_product
