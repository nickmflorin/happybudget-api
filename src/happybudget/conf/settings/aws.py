from happybudget.conf import Environments, config

# Post Copyright Infringement - All Configurations
AWS_ENABLED = False
AWS_ACCESS_KEY_ID = config(
    name='AWS_ACCESS_KEY_ID',
    required=[Environments.PROD, Environments.DEV, Environments.LOCAL],
    default={Environments.TEST: ''},
    enabled=AWS_ENABLED
)

AWS_SECRET_ACCESS_KEY = config(
    name='AWS_SECRET_ACCESS_KEY',
    required=[Environments.PROD, Environments.DEV, Environments.LOCAL],
    default={Environments.TEST: ''},
    enabled=AWS_ENABLED
)

AWS_STORAGE_BUCKET_NAME = config(
    name='AWS_STORAGE_BUCKET_NAME',
    required=[Environments.PROD, Environments.DEV, Environments.LOCAL],
    default={Environments.TEST: ''},
    enabled=AWS_ENABLED
)

AWS_S3_REGION_NAME = config(
    name='AWS_S3_REGION_NAME',
    required=[Environments.PROD, Environments.DEV, Environments.LOCAL],
    default={Environments.TEST: ''},
    enabled=AWS_ENABLED
)

AWS_STORAGE_BUCKET_URL = config(
    name='AWS_STORAGE_BUCKET_URL',
    required=[Environments.PROD, Environments.DEV, Environments.LOCAL],
    default={Environments.TEST: ''},
    enabled=AWS_ENABLED,
    validate=lambda value: (value.endswith(
        '/'), "The URL must end with a trailing slash.")
)

AWS_S3_CUSTOM_DOMAIN = '%s.s3.%s.amazonaws.com' % (
    AWS_STORAGE_BUCKET_NAME, AWS_S3_REGION_NAME)

AWS_DEFAULT_ACL = "public-read"
AWS_DEFAULT_REGION = "us-east-2"
