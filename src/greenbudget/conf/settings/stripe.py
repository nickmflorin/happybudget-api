from greenbudget.conf import Environments, config


STRIPE_API_KEY = config(
    name='STRIPE_API_KEY',
    required=[Environments.PROD, Environments.DEV, Environments.LOCAL],
    default={
        Environments.TEST: 'test_stripe_api_key',
    }
)

STRIPE_API_SECRET = config(
    name='STRIPE_API_SECRET',
    required=[Environments.PROD, Environments.DEV, Environments.LOCAL],
    default={
        Environments.TEST: 'test_stripe_api_secret',
    }
)

GREENBUDGET_STANDARD_PRODUCT_ID = "prod_KUzccoeYwkWGtU"
