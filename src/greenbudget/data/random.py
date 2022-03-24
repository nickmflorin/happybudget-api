import random


def select_random_index(data, **kwargs):
    allow_null = kwargs.pop('allow_null', False)
    if len(data) == 0:
        if not allow_null:
            raise Exception("Cannot select value from empty sequence.")
        return None

    null_frequency = kwargs.pop('null_frequency', 0.0)
    if allow_null is False and null_frequency != 0.0:
        raise Exception(
            "Cannot provide null frequency if null values not allowed.")

    # pylint: disable=chained-comparison
    assert null_frequency <= 1.0 and null_frequency >= 0.0, \
        "The null frequency must be between 0 and 1."

    if null_frequency != 0.0:
        uniform = random.randint(0, 100)
        if uniform >= null_frequency <= null_frequency * 100.0:
            return None
    return random.choice(list(range(len(data))))


def select_random(data, **kwargs):
    index = select_random_index(data, **kwargs)
    if index is None:
        return None
    return data[index]


def select_random_count(data, **kwargs):
    min_count = kwargs.pop('min_count', 0)
    max_count = min(kwargs.pop('max_count', len(data)), len(data))

    assert min_count <= max_count, \
        "The min count must be smaller than or equal to the max count."

    count = kwargs.pop('count', None)
    if count is not None:
        return count
    elif min_count == max_count:
        return min_count
    return random.choice(
        list(range(max_count - min_count + 1))) + min_count


def select_random_set(data, **kwargs):
    total_count = select_random_count(data, **kwargs)

    # We have to be careful with empty datasets, as an empty data set may return
    # a None value which can cause an infinite loop here if we do not return
    # when this is detected.
    current_count = 0
    current_selection = []
    while current_count < total_count:
        choice = select_random(data, **kwargs)
        if choice is None and len(data) == 0:
            return [None]
        elif choice not in current_selection:
            current_selection.append(choice)
            current_count += 1
    return current_selection


def select_random_model_choice(model_cls, attr, **kwargs):
    choices = getattr(model_cls, attr)
    choice = select_random(choices._doubles, **kwargs)
    if choice is not None:
        return choice[0]
    return None
