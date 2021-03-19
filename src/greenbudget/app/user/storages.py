from storages.backends.s3boto3 import S3Boto3Storage


class TempUserImageStorage(S3Boto3Storage):
    bucket_name = 'greenbudget-s3-main'
