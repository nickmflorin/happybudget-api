from timezone_field import TimeZoneField

from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager
from .utils import get_user_from_social_token


def upload_to(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"profile_image_{instance.email.lower().replace(' ','')}.{ext}"
    return f'users/{instance.email.lower()}/profile/{filename}'


class User(AbstractUser):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField(unique=True)
    is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    timezone = TimeZoneField(default='America/New_York')
    profile_image = models.ImageField(upload_to=upload_to, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    objects = UserManager()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ('-created_at', )

    def __str__(self):
        return str(self.get_username())

    @property
    def full_name(self):
        return self.first_name + " " + self.last_name

    def sync_with_social_provider(self, social_user=None, token=None,
            provider=None):
        assert social_user is not None \
            or (token is not None and provider is not None), \
            "Must provide either the social user or the token/provider."
        if social_user is None:
            assert provider == "google", \
                "Unsupported social provider %s." % provider
            social_user = get_user_from_social_token(token, provider)
        if self.first_name is None or self.first_name == "":
            self.first_name = social_user.first_name
        if self.last_name is None or self.last_name == "":
            self.last_name = social_user.last_name
        self.save()
