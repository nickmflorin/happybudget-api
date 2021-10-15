from django.conf import settings

from rest_framework_simplejwt.tokens import SlidingToken
from rest_framework_simplejwt.utils import datetime_to_epoch


class GreenbudgetSlidingToken(SlidingToken):

    def set_exp(self, claim='exp', from_time=None, lifetime=None):
        super().set_exp(claim, from_time, lifetime)
        # Store the iat (issued-at time)
        self.payload['iat'] = datetime_to_epoch(from_time or self.current_time)


class GreenbudgetEmailVerificationSlidingToken(GreenbudgetSlidingToken):
    def set_exp(self, *args, **kwargs):
        kwargs['lifetime'] = settings.EMAIL_VERIFICATION_EXPIRY
        super().set_exp(*args, **kwargs)
