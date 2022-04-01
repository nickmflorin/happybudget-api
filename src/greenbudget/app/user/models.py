import collections
import stripe
from timezone_field import TimeZoneField

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from greenbudget.lib.utils import ensure_iterable

from greenbudget.app import model
from greenbudget.app.authentication.utils import parse_user_id_from_token
from greenbudget.app.billing import StripeCustomer
from greenbudget.app.billing.constants import BillingStatus
from greenbudget.app.io.utils import upload_user_image_to

from .managers import UserManager


def upload_to(instance, filename):
    return upload_user_image_to(
        user=instance,
        filename=filename,
        directory="profile"
    )


SocialUser = collections.namedtuple(
    'SocialUser', ['first_name', 'last_name', 'email'])



@model.model(track_user=False, type='user')
class User(AbstractUser):
    username = None
    first_name = models.CharField(_('First Name'), max_length=150, blank=False)
    last_name = models.CharField(_('Last Name'), max_length=150, blank=False)
    email = models.EmailField(_('Email Address'), blank=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    date_joined = models.DateTimeField(
        _('Date Joined'),
        auto_now_add=True,
        editable=False
    )
    position = models.CharField(max_length=128, null=True, blank=True)
    company = models.CharField(max_length=128, null=True, blank=True)
    address = models.CharField(max_length=30, null=True, blank=True)
    phone_number = models.BigIntegerField(null=True, blank=True)
    timezone = TimeZoneField(default='America/New_York')
    profile_image = models.ImageField(upload_to=upload_to, null=True, blank=True)
    password = models.CharField(_('Password'), max_length=128)
    has_password = models.BooleanField(
        _('Has Password'),
        editable=False,
        default=True,
        help_text=_(
            "Designates whether or not the user was authenticated with social "
            "login."
        )
    )
    is_active = models.BooleanField(
        _('Active'),
        default=True,
        help_text=_("Designates whether this user's account is disabled."),
    )
    is_staff = models.BooleanField(
        _('Staff'),
        default=False,
        help_text=_("Designates whether this user can login to the admin site."),
    )
    is_superuser = models.BooleanField(
        _('Superuser'),
        default=False,
        help_text=_('Designates whether this user is a superuser.'),
    )
    is_first_time = models.BooleanField(
        _('First Time Login'),
        default=True,
        help_text=_('Designates whether this user has logged in yet.'),
    )
    is_verified = models.BooleanField(
        _('Verified'),
        default=False,
        help_text=_(
            'Designates whether this user has verified their email address.'
        ),
    )
    stripe_id = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        editable=False
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ('-last_login', )

    def __str__(self):
        return str(self.get_username())

    @property
    def full_name(self):
        return self.first_name + " " + self.last_name

    @property
    def email_is_verified(self):
        if settings.EMAIL_VERIFICATION_ENABLED is False:
            return True
        return self.is_verified

    @property
    def num_budgets(self):
        return self.budgets.count()

    def sync_with_social_provider(self, social_user=None, token=None,
            provider=None):
        assert social_user is not None \
            or (token is not None and provider is not None), \
            "Must provide either the social user or the token/provider."
        if social_user is None:
            assert provider == "google", \
                "Unsupported social provider %s." % provider
            social_user = User.objects.get_social_user(token, provider)
        if self.first_name is None or self.first_name == "":
            self.first_name = social_user.first_name
        if self.last_name is None or self.last_name == "":
            self.last_name = social_user.last_name

    def cache_stripe_from_token(self, token_obj):
        """
        Uses the Stripe information embedded in the provided token to cache
        the Stripe data on the :obj:`StripeCustomer` associated with the
        :obj:`User` such that subsequent attempts to access Stripe data for
        the :obj:`User` do not perform an HTTP request to Stripe's API.
        """
        if parse_user_id_from_token(token_obj) != self.id:
            raise Exception(
                "The provided token is not associated with this user.")
        if self.stripe_customer is not None:
            self.stripe_customer.cache_from_token(token_obj)
        elif self.stripe_id is not None and self.is_authenticated \
                and self.email_is_verified:
            self._stripe_customer = StripeCustomer.from_token(
                token_obj=token_obj,
                user=self
            )

    def flush_stripe_cache(self):
        """
        Flushes the Stripe data on the :obj:`StripeCustomer` associated with the
        :obj:`User` such that subsequent attempts to access Stripe data for the
        :obj:`User` perform an HTTP request to Stripe's API.
        """
        if self.stripe_customer is not None:
            self.stripe_customer.flush_cache()

    def update_or_create_stripe_customer(self, metadata=None):
        """
        Updates or creates the Stripe customer data associated with the
        :obj:`User`.

        Note:
        ----
        This method is currently not used, but is left here for future use case
        as we are going to eventually rely less on the automated aspects of
        Stripe's payment processing system.
        """
        customer_kwargs = {
            'name': self.full_name,
            'email': self.email,
            'metadata': {'user_id': self.pk}
        }
        # TODO: Eventually we will need to include the address in the Stripe
        # customer data when we have split the address field into it's
        # appropriate component parts.
        if metadata is not None:
            customer_kwargs['metadata'].update(metadata)

        if not self.stripe_id:
            stripe_customer = stripe.Customer.create(**customer_kwargs)
            self.stripe_id = stripe_customer.id
        else:
            stripe.Customer.modify(self.stripe_id, **customer_kwargs)

        # Refresh / populate the stripe_customer attribute.
        self.stripe_customer = self.stripe_id
        return self.stripe_customer

    def get_or_create_stripe_customer(self, metadata=None):
        """
        Retrieves or creates the Stripe customer data associated with the
        :obj:`User`.

        Note:
        ----
        This method is currently not used, but is left here for future use case
        as we are going to eventually rely less on the automated aspects of
        Stripe's payment processing system.
        """
        if self.stripe_id is None:
            return self.update_or_create_stripe_customer(metadata=metadata)
        return self.stripe_customer

    @property
    def stripe_customer(self):
        """
        Returns the :obj:`StripeCustomer` associated with the :obj:`User`.
        """
        if not hasattr(self, '_stripe_customer') and self.stripe_id:
            self._stripe_customer = StripeCustomer(self)
        return getattr(self, '_stripe_customer', None)

    @stripe_customer.setter
    def stripe_customer(self, value):
        if isinstance(value, str):
            self.stripe_id = value
        elif isinstance(value, stripe.Customer):
            self.stripe_id = value['id']
        elif isinstance(value, StripeCustomer):
            self.stripe_id = value.stripe_id
            self._stripe_customer = value
            return
        else:
            raise ValueError("Invalid stripe_customer %s" % value)

        self._stripe_customer = StripeCustomer(self)

    @property
    def billing_status(self):
        if self.stripe_customer:
            return self.stripe_customer.billing_status
        return None

    @property
    def product_id(self):
        if self.stripe_customer:
            return self.stripe_customer.product_id
        return None

    def has_product(self, product):
        assert product is not None, "Product must be non-null."
        if product == '__any__':
            return self.billing_status == BillingStatus.ACTIVE \
                and self.product_id is not None
        return self.billing_status == BillingStatus.ACTIVE \
            and self.product_id in ensure_iterable(product)
