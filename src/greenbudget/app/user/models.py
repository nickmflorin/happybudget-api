from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['emai']

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ('-created_at', )

    def __str__(self):
        return str(self.get_username())

    @property
    def full_name(self):
        if self.first_name is not None and self.first_name != "":
            if self.last_name is not None and self.last_name != "":
                return "%s %s" % (self.first_name, self.last_name)
            return self.first_name
        if self.last_name is not None and self.last_name != "":
            return self.last_name
        return ""
