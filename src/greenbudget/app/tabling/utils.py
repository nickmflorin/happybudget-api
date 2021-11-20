import functools
import math
import string


class BoundsError(Exception):
    def __init__(self, message):
        self.message = message


class InconsistentOrderingError(Exception):
    def __init__(self, a, b, message=None):
        self._a = a
        self._b = b
        self._message = message

    def __str__(self):
        if self._message is None:
            return "Inconsistent ordering between %s and %s!" \
                % (self._a, self._b)
        return "Inconsistent ordering between %s and %s: %s" \
            % (self._a, self._b, self._message)


def has_index(a_string, index):
    # Less confusing alternative to always checking length - 1.
    try:
        a_string[index]
    except IndexError:
        return False
    return True


def char_index(char):
    return string.ascii_lowercase.index(char.lower())


def get_midpoint(upper, lower=None, floor=False):
    if upper is None:
        raise BoundsError(message="Upper bound cannot be None.")
    elif lower == upper:
        raise BoundsError(message="Bounds cannot be equal.")

    upper = upper.lower()
    lower = (lower or "a").lower()

    if [lower, upper] == ['a', 'b']:
        if floor:
            return 'a'
        return 'b'

    # The bounds cannot be consecutive.
    if char_index(lower) + 1 == char_index(upper):
        raise BoundsError(message="Bounds cannot be consecutive.")

    float_midpoint = (char_index(lower) + char_index(upper)) / 2
    if floor:
        return string.ascii_lowercase[math.floor(float_midpoint)]
    return string.ascii_lowercase[math.ceil(float_midpoint)]


def get_bounds(string_a, string_b):
    if not string_a < string_b:
        raise InconsistentOrderingError(
            a=string_a,
            b=string_b,
            message="Strings are not lexographically in order."
        )
    elif string_a == "" or string_b == "":
        raise InconsistentOrderingError(
            a=string_a,
            b=string_b,
            message="Strings cannot be of length 0."
        )

    # Loop over longer list if the lengths differ.
    longer_string = string_a
    shorter_string = string_b
    base = 'a'
    if len(string_b) > len(string_a):
        longer_string = string_b
        shorter_string = string_a
        base = 'b'

    encountered = []
    for i, char_base in enumerate(longer_string):
        if not has_index(shorter_string, i):
            # Note: Since we are enforcing that the two strings are
            # lexographically in order, the only way that A is longer than
            # B is if the last character of B is different from that of the
            # character in A at that index: A = 'abcd', B = 'abf' - this means
            # that the upper bound will never be None.
            if base != 'b':
                raise InconsistentOrderingError(
                    a=string_a,
                    b=string_b,
                    message="Strings are not lexographically in order."
                )
            return ''.join(encountered), i, [None, char_base]
        elif char_base != shorter_string[i]:
            if base == 'b':
                return ''.join(encountered), i, [shorter_string[i], char_base]
            return ''.join(encountered), i, [char_base, shorter_string[i]]
        encountered.append(char_base)

    # This should only happen if both strings are empty strings, or the same
    # string, both of which we assert is not the case at the beginning of this
    # method.
    raise InconsistentOrderingError(string_a, string_b)


def lexographically_consecutive(a, b):
    """
    Returns whether or not the two characters are alphabetically consecutive.
    """
    assert b is not None
    if a is None:
        return False
    return char_index(a) + 1 == char_index(b)


def validate_order(value):
    if not isinstance(value, str):
        raise Exception("Order must be a string, not %s." % type(value))
    value = value.lower()
    if not all([x in string.ascii_lowercase for x in value]):
        raise Exception("String must only contain alphabet characters!")
    return value


def validate_result(func):
    @functools.wraps(func)
    def decorator(lower=None, upper=None):
        result = func(lower=lower, upper=upper)
        if result == lower or result == upper:
            import ipdb
            ipdb.set_trace()
            raise InconsistentOrderingError(
                lower,
                upper,
                message='Result %s equals one of the bounds.' % result
            )
        return result
    return decorator


@validate_result
def lexographic_midpoint(lower=None, upper=None):
    """
    Algorithm that returns a string that occurs lexographically in between
    the two provided strings, such that there is always room between the
    first string and the midpoint, and the second string and the midpoint,
    to insert additional strings in lexographic order.

    Source:
    https://stackoverflow.com/questions/38923376/
    return-a-new-string-that-sorts-between-two-given-strings/38927158#38927158

    Methodology:
    -----------
    The algorithm logic is based on starting at the left of both strings and
    copying the characters as we move right, stopping at the first set of
    characters that differ or the end of the left string.

    From this, we create the base string, the differing index and the bounds:

    Base String:      The characters that are the same between the two strings
                      up until the differing index.
    Differing Index:  The numeric index location at which the two strings first
                      have differing characters.
    Bounds:           The left (if applicable) and right characters at the
                      differing index.

    Examples:

    - A = abcd, B = abf
      Base String = ab, Bounds = (h, i), Differing Index = 2
    - A = abc, B = abcah
      Base String = abc, Bounds = (None, a), Differing Index = 3

    Then, given the bounds, we have 3 potentially different cases:

    (1) The two different characters in the bounds are lexographically
        consecutive.

        In this case, we copy the left character and then append the character
        halfway between the next character from the left string and the end of
        the alphabet.

        If the next left character is a z, we continue to append characters
        until the first non z character is found.  Appending a z to the end
        of the lexographical midpoint string would otherwise result in a
        situation where two ordered strings have no midpoint.

    (2) The right character in the bound is an a or b.

        You should never create a string by appending an 'a' to the left string,
        because that would create two lexicographically consecutive strings at
        some point in the future, inbetween which no further strings could be
        added.

        The solution is to always append an additional character, halfway
        inbetween the beginning of the alphabet and the next character from
        the right string.

    (3) Basic situation

        Neither (1) or (2) apply.

        The new string is then created by appending the character that is
        halfway in the alphabet between the left bound (or beginning of the
        alphabet) and the right bound:
    """
    # If no arguments are supplied, just return the lexigraphic midpoint of
    # the entire alphabet.
    if not lower and not upper:
        return get_midpoint("z", lower="a")
    elif not lower and upper:
        return lexographic_midpoint(lower="a", upper=upper)
    elif not upper and lower:
        return lexographic_midpoint(lower=lower, upper="z")

    string_a = validate_order(lower)
    string_b = validate_order(upper)

    if not string_a < string_b:
        raise InconsistentOrderingError(
            string_a, string_b, message='Bounds are not in correct order.')

    base, differing_index, bounds = get_bounds(string_a, string_b)

    # Case 2
    if bounds[1] in ('a', 'b'):
        # If the right string (B) is a or b, the left string (A) must be less
        # characters than B because A is lexographically "less than" (i.e.
        # occurs before alphabetically) B, and the algorithm prevents the
        # characters a or b from being added to the end.
        if len(string_a) > len(string_b):
            raise InconsistentOrderingError(string_a, string_b)
        try:
            next_character = string_b[differing_index + 1]
        except IndexError:
            # This happens when, for example, A = abc, B = abcb.
            base = base + bounds[1]
        else:
            base = base + bounds[1] + next_character
            # Continuing adding the next character in B to the base until we
            # encounter either the end of B or a character that is not a or b.
            while next_character in ('a', 'b'):
                differing_index += 1
                try:
                    next_character = string_b[differing_index + 1]
                except IndexError:
                    break
                base = base + next_character

        try:
            base = base[:-1] + get_midpoint(base[-1], lower="a", floor=True)
        except BoundsError as e:
            raise InconsistentOrderingError(
                a=string_a,
                b=string_b,
                message=e.message
            )

        # This can happen if B ends with all a's and b's, thus the string will
        # continue to pluck off the last element until there are none left.
        # This means that the strings would be, for example, A = abc, B = abcab.
        # In this case, we have to append an additional character halfway
        # through the alphabet.
        if base[-1] in ('a', 'b'):
            return base + get_midpoint("z", lower="a")
        return base

    # Case 1
    elif lexographically_consecutive(bounds[0], bounds[1]):
        # Edge case where we are finding the midpoint between a y[?][?]... and
        # end of the alphabet (z) -> i.e. ynt and z.
        if base == "" and bounds[1] == "z":
            if string_a[-1] == "y":
                return string_a + get_midpoint("z", lower="a")
            try:
                return string_a + get_midpoint("z", lower=string_a[-1])
            except BoundsError as e:
                raise InconsistentOrderingError(
                    a=string_a,
                    b=string_b,
                    message=e.message
                )

        # This will happen in the case of A = abh, B = abit because the bounds
        # will be [h, i] and h is at the end of A.  In this case, we add the
        # left bound and then the midpoint of the alphabet.
        if not has_index(string_a, differing_index + 1):
            # This algorithm should ensure that if we are at the end of A,
            # then the lower bound should be the last character in A.  This
            # is because otherwise, the strings would not have any room to
            # insert in between, which this algorithm prevents.  For an example,
            # this would happen if A = abc, B = abd, which this algorithm
            # prevents.
            if bounds[0] != string_a[-1]:
                raise InconsistentOrderingError(string_a, string_b)
            try:
                return base + bounds[0] + get_midpoint("z", lower="a")
            except BoundsError as e:
                raise InconsistentOrderingError(
                    a=string_a,
                    b=string_b,
                    message=e.message
                )

        if string_a.endswith('z'):
            return string_a + get_midpoint("z", lower="a")

        def add_and_return(base, bounds):
            try:
                if string_a[len(base)] == 'z':
                    base = base + string_a[len(base)]
                    bounds[0] = string_a[len(base)]
                    return add_and_return(base, bounds)
                try:
                    return base + get_midpoint("z", lower=string_a[len(base)])
                except BoundsError as e:
                    raise InconsistentOrderingError(
                        a=string_a,
                        b=string_b,
                        message=e.message
                    )
            except IndexError:
                return base + get_midpoint("z", lower="a")

        base = base + bounds[0]
        return add_and_return(base, bounds)

    # Case 3
    else:
        return base + get_midpoint(bounds[1], lower=bounds[0])


def order_after(count, last_order=None):
    ordering = []
    if count != 0:
        # If the last order is None, start the ordering off at the midpoint of
        # the alphabet.  Otherwise, start it off at the midpoint bewteen the
        # last order and the end of the alphabet.
        if last_order is None:
            ordering.append(lexographic_midpoint())
        else:
            ordering.append(lexographic_midpoint(lower=last_order))
        for i in range(count - 1):
            ordering.append(lexographic_midpoint(lower=ordering[i]))
    return ordering
