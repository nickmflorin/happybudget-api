from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import Throttled


class RateLimitedError(Throttled):
    default_detail = _("Request limit exceeded.")
    default_code = "rate_limited"
