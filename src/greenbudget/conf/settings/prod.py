"""
Settings configuration file for production environment.
"""
from greenbudget.conf import Environments

from .base import *  # noqa

ENVIRONMENT = Environments.PROD
