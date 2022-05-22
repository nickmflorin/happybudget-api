import collections
import datetime
import logging
import requests
import stripe
from timezone_field import TimeZoneField

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from happybudget.conf import suppress_with_setting

from happybudget.lib.utils import ensure_iterable
from happybudget.lib.utils.dateutils import ensure_datetime
from happybudget.lib.utils.urls import add_query_params_to_url

from happybudget.app import model
from happybudget.app.authentication.exceptions import (
    InvalidSocialProvider, InvalidSocialToken)
from happybudget.app.authentication.utils import parse_user_id_from_token
from happybudget.app.billing import StripeCustomer
from happybudget.app.billing.constants import BillingStatus
from happybudget.app.io.utils import parse_image_filename, parse_filename

from .mail import EmailVerificationMail, PasswordRecoveryMail
from .mixins import UserAuthenticationMixin
from .managers import UserManager


logger = logging.getLogger('happybudget')


def upload_to(instance, filename):
    return instance.upload_image_to(
        filename=filename,
        directory="profile"
    )


SocialUser = collections.namedtuple(
    'SocialUser', ['first_name', 'last_name', 'email'])


@model.model(type='user')
class User(UserAuthenticationMixin, AbstractUser):
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
    def now_in_timezone(self):
        return self.in_timezone(datetime.datetime.now())

    @property
    def today_in_timezone(self):
        return self.in_timezone(datetime.date.today())

    def in_timezone(self, value, force_date=False, force_datetime=False):
        assert not (force_date and force_datetime), \
            "Both date and datetime formatting cannot be forced.s"
        aware = ensure_datetime(value).replace(tzinfo=self.timezone)
        # Note: This means that string provided dates will be returned as
        # datetimes unless parameter is specified.
        if type(value) is datetime.date or force_date and not force_datetime:
            return aware.date()
        return aware

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
        # pylint: disable=import-outside-toplevel
        from happybudget.app.budget.models import Budget
        return Budget.objects.filter(created_by=self).count()

    @property
    def num_templates(self):
        # pylint: disable=import-outside-toplevel
        from happybudget.app.template.models import Template
        return Template.objects.filter(community=False, created_by=self).count()

    @property
    def num_collaborating_budgets(self):
        return self.collaborating_budgets.count()

    @property
    def collaborating_budgets(self):
        # pylint: disable=import-outside-toplevel
        from happybudget.app.budget.models import Budget
        return Budget.objects.filter(pk__in=[
            collaboration.object_id
            for collaboration in self.collaborations.filter(
                content_type=ContentType.objects.get_for_model(Budget)
            ).only('object_id')
        ])

    @property
    def num_archived_budgets(self):
        return self.archived_budgets.count()

    @property
    def archived_budgets(self):
        # pylint: disable=import-outside-toplevel
        from happybudget.app.budget.models import Budget
        return Budget.objects.filter(archived=True, created_by=self)

    @suppress_with_setting('SOCIAL_AUTHENTICATION_ENABLED', exc=True)
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

    @suppress_with_setting('BILLING_ENABLED', exc=True)
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

    @suppress_with_setting('BILLING_ENABLED', exc=True)
    def flush_stripe_cache(self):
        """
        Flushes the Stripe data on the :obj:`StripeCustomer` associated with the
        :obj:`User` such that subsequent attempts to access Stripe data for the
        :obj:`User` perform an HTTP request to Stripe's API.
        """
        if self.stripe_customer is not None:
            self.stripe_customer.flush_cache()

    @suppress_with_setting('BILLING_ENABLED', exc=True)
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

    @suppress_with_setting('BILLING_ENABLED', exc=True)
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
        suppress_with_setting.raise_if_suppressed(
            attr='BILLING_ENABLED',
            func='stripe_customer'
        )
        if not hasattr(self, '_stripe_customer') and self.stripe_id:
            self._stripe_customer = StripeCustomer(self)
        return getattr(self, '_stripe_customer', None)

    @stripe_customer.setter
    def stripe_customer(self, value):
        suppress_with_setting.raise_if_suppressed(
            attr='BILLING_ENABLED',
            func='stripe_customer'
        )
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
        if settings.BILLING_ENABLED and self.stripe_customer:
            return self.stripe_customer.billing_status
        return None

    @property
    def product_id(self):
        if settings.BILLING_ENABLED and self.stripe_customer:
            return self.stripe_customer.product_id
        return None

    @suppress_with_setting('BILLING_ENABLED', exc=True)
    def has_product(self, product):
        assert product is not None, "Product must be non-null."
        if product == '__any__':
            return self.billing_status == BillingStatus.ACTIVE \
                and self.product_id is not None
        return self.billing_status == BillingStatus.ACTIVE \
            and self.product_id in ensure_iterable(product)

    SOCIAL_USER_LOOKUPS = {
        'google': 'get_google_user'
    }

    @classmethod
    @suppress_with_setting("SOCIAL_AUTHENTICATION_ENABLED", exc=True)
    def get_google_user(cls, token):
        assert settings.GOOGLE_OAUTH_API_URL is not None, \
            "Configuration parameter `GOOGLE_OAUTH_API_URL` is not defined."
        url = add_query_params_to_url(
            url=settings.GOOGLE_OAUTH_API_URL,
            id_token=token
        )
        try:
            response = requests.get(url)
        except requests.RequestException as e:
            logger.error("Network Error Validating Google Token: %s" % e)
            raise InvalidSocialToken() from e
        else:
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                logger.error("HTTP Error Validating Google Token: %s" % e)
                raise InvalidSocialToken() from e
            else:
                return SocialUser(
                    first_name=response.json()['given_name'],
                    last_name=response.json()['family_name'],
                    email=response.json()['email']
                )

    @classmethod
    @suppress_with_setting("SOCIAL_AUTHENTICATION_ENABLED", exc=True)
    def get_social_user(cls, token, provider):
        try:
            method_name = cls.SOCIAL_USER_LOOKUPS[provider]
        except KeyError as e:
            raise InvalidSocialProvider() from e
        return getattr(cls, method_name)(token)

    @property
    def storage_directory(self):
        return f'users/{self.pk}'

    @property
    def temp_storage_directory(self):
        return f'{self.storage_directory}/temp'

    def upload_temp_image_to(self, filename, directory=None, **kwargs):
        filename, ext = parse_image_filename(filename, **kwargs)
        if directory is not None:
            return f'{self.temp_storage_directory}/{directory}/{filename}'
        return f'{self.temp_storage_directory}/{filename}'

    def upload_image_to(self, filename, directory=None, **kwargs):
        filename, ext = parse_image_filename(filename, **kwargs)
        if directory is not None:
            return f'{self.storage_directory}/{directory}/{filename}'
        return f'{self.storage_directory}/{filename}'

    def upload_temp_file_to(self, filename, directory=None, **kwargs):
        filename, _ = parse_filename(filename, **kwargs)
        if directory is not None:
            return f'{self.temp_storage_directory}/{directory}/{filename}'
        return f'{self.temp_storage_directory}/{filename}'

    def upload_file_to(self, filename, directory=None, **kwargs):
        filename, _ = parse_filename(filename, **kwargs)
        if directory is not None:
            return f'{self.storage_directory}/{directory}/{filename}'
        return f'{self.storage_directory}/{filename}'

    @suppress_with_setting("EMAIL_VERIFICATION_ENABLED")
    @suppress_with_setting("EMAIL_ENABLED")
    def send_email_verification_email(self, token=None):
        return EmailVerificationMail(self, token=token).send()

    @suppress_with_setting("EMAIL_ENABLED")
    def send_password_recovery_email(self, token=None):
        return PasswordRecoveryMail(self, token=token).send()
