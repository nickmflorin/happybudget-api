import os


def construct_unique_name(name, names, with_extensions=True,
        case_sensitive=True):
    """
    Constructs a unique name by appending (i) to the end of the name until
    it is not present in the provided set of names, in order to prevent
    duplication of names within the provided set of names.

    Parameters:
    ----------
    name: :obj:`str`
        The base name for which the unique suffixes should be appended to in
        the case that it is not unique.  This value can either be a generic
        name or a filename with an extension.

    names: :obj:`list`, :obj:`tuple`
        A iterable of names that already exist.  If the provided name is in
        this list, it will be suffixed to prevent if from being a duplicate.
        The names can either be generic names or can each be a filename with
        an extension.

    with_extensions: :obj:`bool`
        If True, the extensions of the names will be included to determine
        the uniqueness of the name.  If False, the extensions of the names
        will not be included in the uniqueness check, and thus are irrelevant.

        Default: True

        construct_unique_name(
            "file1.pdf", ["file1.jpg"], with_extensions=False)
        >>> file1(1).pdf

        construct_unique_name("file1.pdf", ["file1.jpg"], with_extensions=True)
        >>> file1.pdf

    case_sensitive: :obj:`bool`
        Whether or not the character case should be taken into account when
        determining the uniqueness of the provided name.

        Default: True
    """
    base, extension = os.path.splitext(name)
    bases = [os.path.splitext(nm)[0] for nm in names]

    def is_unique(value):
        if with_extensions:
            if case_sensitive:
                if value not in names:
                    return True
            else:
                if value.lower() not in [nm.lower() for nm in names]:
                    return True
        else:
            if case_sensitive:
                if os.path.splitext(value)[0] not in bases:
                    return True
            else:
                if os.path.splitext(value)[0].lower() not in [
                        b.lower() for b in bases]:
                    return True
        return False

    if is_unique(name):
        return name

    count = 1
    while True:
        # TODO: Figure out a way to make the case sensitivity not apply to
        # the extension.
        suffixed = suffix_name_with_count(base, count, ext=extension)
        if is_unique(suffixed):
            return suffixed
        count += 1


def parse_name_and_count(name):
    """
    Parses the filename, the count and the extension from a filename that
    might have it's duplicity denoted with notation including an integer
    of it's count surrounded by paranthesis.  The mechanics of the method
    step through the name in the reverse direction, which is safer than a
    regex solution or string splitting solution.

    The utility works for both generic names and names that might include a
    file extension.

    Usage:
    -----
    >>> parse_name_and_count("foo(1).pdf")
    >>> ("foo", 1, ".pdf")

    >>> parse_name_and_count("foo")
    >>> ("foo", None, "")

    >>> parse_name_and_count("foo(4)")
    >>> ("foo", 4)
    """
    base, ext = os.path.splitext(name)

    reverse_name = base[::-1].strip()
    if len(reverse_name) < 3 or reverse_name[0] != ")":
        return base, None, ext

    def reverse_engineer_count(integers):
        if len(integers) == 0:
            return None
        numbers = integers[:]
        numbers.reverse()
        return int("".join(["%s" % num for num in numbers]))

    index = 1
    integers = []
    while len(reverse_name) > index:
        char = reverse_name[index]
        try:
            char_int = int(char)
        except ValueError:
            break
        else:
            integers.append(char_int)
            index += 1

    if index < len(reverse_name) and reverse_name[index] == "(":
        name = "".join(reverse_name[index + 1:][::-1])
        return name, reverse_engineer_count(integers), ext
    return base, None, ext


def suffix_name_with_count(name, count, ext=""):
    """
    Includes the integer count as a suffix to the name.

    If there is an extension on the name, that will be used.  Otherwise, the
    provided extension will be used (if it is not an empty string).

    Usage:
    ------
    >>> suffix_name_with_count("foo", 4)
    >>> foo(4)

    >>> suffix_name_with_count("foo.pdf", 5)
    >>> foo(5).pdf
    """
    base, existing_ext = os.path.splitext(name)
    if existing_ext:
        return "%s(%s)%s" % (base, count, existing_ext)
    return "%s(%s)%s" % (name, count, ext)


def increment_name_count(name):
    """
    Increments the count appended to the end of a name in the case that it
    is a duplicate.

    This can be used for both generic names or filenames with extensions.

    Usage:
    ------
    >>> increment_name_count("foo(1).pdf")
    >>> foo(2).pdf

    >>> increment_name_count("foo(2)")
    >>> foo(3)

    >>> increment_name_count("foo")
    >>> foo(1)
    """
    base, count, ext = parse_name_and_count(name)
    new_count = count + 1 if count is not None else 1
    return suffix_name_with_count(base, new_count, ext)
