import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


UPPERCASE = 'A-Z'
LOWERCASE = 'a-z'
NUMBER = '0-9'


class Validator:
    def __init__(self,
        error_message='The provided password is invalid.',
        code='invalid_password'
    ):
        self.code = code
        self.error_message = error_message

    def fail(self, **kwargs):
        raise ValidationError(
            _(self.error_message),
            code=self.code,
            **kwargs
        )


class MinLengthValidator(Validator):
    def __init__(self, min_count=8, **kwargs):
        super().__init__(**kwargs)
        self.min_count = min_count

    def validate(self, password, user=None):
        if len(password) < self.min_count:
            self.fail(params={'min_count': self.min_count})


class MinCharacterCountRegexValidator(MinLengthValidator):
    def __init__(self, characters=None, **kwargs):
        super().__init__(**kwargs)
        self.characters = characters or "|".join([
            UPPERCASE,
            LOWERCASE,
            NUMBER
        ])

    def validate(self, password, user=None):
        chars = re.findall('[%s]' % self.characters, password)
        if len(chars) < self.min_count:
            self.fail(params={'min_count': self.min_count})


class SpecialCharRegexValidator(Validator):
    def validate(self, password, user=None):
        pattern = re.compile('[@_!#$%^&*()<>?/\|}{~:]')  # noqa
        searched = pattern.search(password)
        if not searched:
            self.fail()


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
    SpecialCharRegexValidator(
        error_message='Password must contain at least 1 special character.'
    )
]
