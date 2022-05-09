from django.contrib.auth.models import AnonymousUser as DAnonymous

from .mixins import UserAuthenticationMixin


class AnonymousUser(DAnonymous, UserAuthenticationMixin):
    is_active = False
    is_verified = False
