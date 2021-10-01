import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


UPPERCASE = 'A-Z'
LOWERCASE = 'a-z'
NUMBER = '0-9'
SPECIAL_CHARACTER = '!@#$%&_='


class MinCharacterCountRegexValidator:
    def __init__(self,
        characters=None,
        min_count=1,
        error_message='The provided password is invalid.',
        code='invalid_password'
    ):
        self.code = code
        self.characters = characters or "|".join([
            UPPERCASE,
            LOWERCASE,
            NUMBER,
            SPECIAL_CHARACTER
        ])
        self.min_count = min_count
        self.error_message = error_message

    def validate(self, password, user=None):
        chars = re.findall('[%s]' % self.characters, password)
        if len(chars) < self.min_count:
            raise ValidationError(
                _(self.error_message),
                code=self.code,
                params={'min_count': self.min_count},
            )


PASSWORD_VALIDATORS = [
    MinCharacterCountRegexValidator(
        min_count=8,
        error_message='Password must be at least 8 characters.'
    ),
    MinCharacterCountRegexValidator(
        min_count=1,
        characters=LOWERCASE,
        error_message='Password must contain at least 1 lowercase character.'
    ),
    MinCharacterCountRegexValidator(
        min_count=1,
        characters=UPPERCASE,
        error_message='Password must contain at least 1 uppercase character.'
    ),
    MinCharacterCountRegexValidator(
        min_count=1,
        characters=NUMBER,
        error_message='Password must contain at least 1 number.'
    ),
    MinCharacterCountRegexValidator(
        min_count=1,
        characters=SPECIAL_CHARACTER,
        error_message='Password must contain at least 1 special character.'
    )
]
