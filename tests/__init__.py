import pytest


def need_to_write(func):
    return pytest.mark.skip(f"Test {func.__name__} needs to be written.")(func)
