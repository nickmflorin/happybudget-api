# -*- coding: utf-8 -*-
from setuptools import setup

package_dir = \
{'': 'src'}

packages = \
['greenbudget',
 'greenbudget.app',
 'greenbudget.app.account',
 'greenbudget.app.account.migrations',
 'greenbudget.app.actual',
 'greenbudget.app.actual.migrations',
 'greenbudget.app.authentication',
 'greenbudget.app.authentication.migrations',
 'greenbudget.app.budget',
 'greenbudget.app.budget.migrations',
 'greenbudget.app.budget_item',
 'greenbudget.app.budget_item.migrations',
 'greenbudget.app.comment',
 'greenbudget.app.comment.migrations',
 'greenbudget.app.common',
 'greenbudget.app.contact',
 'greenbudget.app.contact.migrations',
 'greenbudget.app.history',
 'greenbudget.app.history.migrations',
 'greenbudget.app.jwt',
 'greenbudget.app.subaccount',
 'greenbudget.app.subaccount.migrations',
 'greenbudget.app.user',
 'greenbudget.app.user.migrations',
 'greenbudget.conf',
 'greenbudget.conf.settings',
 'greenbudget.lib',
 'greenbudget.lib.django_utils',
 'greenbudget.lib.logging',
 'greenbudget.lib.model_tracker',
 'greenbudget.lib.rest_framework_utils',
 'greenbudget.lib.utils',
 'greenbudget.management',
 'greenbudget.management.commands']

package_data = \
{'': ['*'], 'greenbudget': ['templates/*']}

install_requires = \
['Django>=3.1.6,<4.0.0',
 'Pillow>=8.1.2,<9.0.0',
 'PyJWT==1.7.1',
 'boto3>=1.17.32,<2.0.0',
 'cryptography>=3.4.6,<4.0.0',
 'dj-database-url==0.5.0',
 'django-colorful>=1.3,<2.0',
 'django-cors-headers>=3.7.0,<4.0.0',
 'django-extensions>=3.1.1,<4.0.0',
 'django-model-utils>=4.1.1,<5.0.0',
 'django-phonenumber-field[phonenumbers]>=5.0.0,<6.0.0',
 'django-polymorphic>=3.0.0,<4.0.0',
 'django-ratelimit>=3.0.1,<4.0.0',
 'django-rest-polymorphic>=0.1.9,<0.2.0',
 'django-storages>=1.11.1,<2.0.0',
 'django-timezone-field>=4.1.1,<5.0.0',
 'djangorestframework-filters==1.0.0.dev0',
 'djangorestframework==3.11.1',
 'djangorestframework_simplejwt==4.3.0',
 'gunicorn>=20.0.4,<21.0.0',
 'psycopg2-binary>=2.8.6,<3.0.0',
 'psycopg2>=2.8.6,<3.0.0',
 'pytest>=6.2.2,<7.0.0',
 'python-dateutil>=2.8.1,<3.0.0',
 'python-dotenv>=0.15.0,<0.16.0',
 'tox>=3.20.1,<4.0.0']

entry_points = \
{'console_scripts': ['manage = greenbudget.lib.django_utils.cli:main']}

setup_kwargs = {
    'name': 'greenbudget',
    'version': '0.1.0',
    'description': 'Backend Application for Green Buget Application',
    'long_description': None,
    'author': 'nickmflorin',
    'author_email': 'nickmflorin@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/Saturation-IO/greenbudget-api',
    'package_dir': package_dir,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
