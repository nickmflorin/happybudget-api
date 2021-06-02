from greenbudget.conf import Environments, config

AWS_ACCESS_KEY_ID = config(
    name='AWS_ACCESS_KEY_ID',
    required=[Environments.PROD, Environments.DEV, Environments.LOCAL],
    default={
        Environments.TEST: '',
    }
)

AWS_SECRET_ACCESS_KEY = config(
    name='AWS_SECRET_ACCESS_KEY',
    required=[Environments.PROD, Environments.DEV, Environments.LOCAL],
    default={
        Environments.TEST: '',
    }
)

AWS_STORAGE_BUCKET_NAME = config(
    name='AWS_STORAGE_BUCKET_NAME',
    required=[Environments.PROD, Environments.DEV, Environments.LOCAL],
    default={
        Environments.TEST: '',
    }
)

AWS_S3_REGION_NAME = config(
    name='AWS_S3_REGION_NAME',
    required=[Environments.PROD, Environments.DEV, Environments.LOCAL],
    default={
        Environments.TEST: '',
    }
)

AWS_S3_CUSTOM_DOMAIN = '%s.s3.%s.amazonaws.com' % (
    AWS_STORAGE_BUCKET_NAME, AWS_S3_REGION_NAME)

AWS_DEFAULT_ACL = "public-read"
AWS_DEFAULT_REGION = "us-east-2"
