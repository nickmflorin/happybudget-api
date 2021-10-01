from django.conf import settings


def validate_password(password):
    for validator in settings.PASSWORD_VALIDATORS:
        validator.validate(password)
