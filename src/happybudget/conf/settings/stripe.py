from happybudget.conf import Environments, config


# Post Copyright Infringement - All Configurations
BILLING_ENABLED = None

STRIPE_API_KEY = config(
    name='STRIPE_API_KEY',
    required=[Environments.PROD, Environments.DEV, Environments.LOCAL],
    default={
        Environments.TEST: 'test_stripe_api_key',
    },
    enabled=BILLING_ENABLED
)

STRIPE_API_SECRET = config(
    name='STRIPE_API_SECRET',
    required=[Environments.PROD, Environments.DEV, Environments.LOCAL],
    default={
        Environments.TEST: 'test_stripe_api_secret',
    },
    enabled=BILLING_ENABLED
)
