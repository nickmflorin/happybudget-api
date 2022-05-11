#!/usr/bin/env python
import os
import sys


def main():
    os.environ.setdefault(
        'DJANGO_SETTINGS_MODULE', 'happybudget.conf.settings.local')
    try:
        # pylint: disable=import-outside-toplevel
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    settings_module = os.environ["DJANGO_SETTINGS_MODULE"]

    arguments = sys.argv[:]
    if arguments == ['src/manage.py', 'runserver'] \
            and settings_module == 'happybudget.conf.settings.local':
        arguments = arguments + ['local.happybudget.io:8000']

    execute_from_command_line(arguments)


if __name__ == '__main__':
    main()
