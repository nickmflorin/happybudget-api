from model_utils import Choices

from django.db import models

from greenbudget.lib.utils import conditionally_separate_strings
from greenbudget.app.io.utils import upload_user_image_to


def upload_to(instance, filename):
    return upload_user_image_to(
        user=instance.user,
        filename=filename,
        directory="contacts"
    )


class Contact(models.Model):
    type = "contact"
    first_name = models.CharField(max_length=30, null=True)
    last_name = models.CharField(max_length=30, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(
        to='user.User',
        on_delete=models.CASCADE,
        related_name="contacts"
    )
    TYPES = Choices(
        (0, "contractor", "Contractor"),
        (1, "employee", "Employee"),
        (2, "vendor", "Vendor"),
    )
    contact_type = models.IntegerField(choices=TYPES, null=True)
    position = models.CharField(max_length=128, null=True)
    company = models.CharField(max_length=128, null=True)
    city = models.CharField(max_length=30, null=True)
    phone_number = models.CharField(max_length=128, null=True)
    email = models.EmailField(null=True)
    rate = models.IntegerField(null=True)
    image = models.ImageField(upload_to=upload_to, null=True)

    class Meta:
        get_latest_by = "updated_at"
        ordering = ('created_at', )
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"

    def __str__(self):
        return "<{cls} id={id}, email={email}>".format(
            cls=self.__class__.__name__,
            id=self.pk,
            email=self.email,
        )

    @property
    def full_name(self):
        return conditionally_separate_strings([self.first_name, self.last_name])
