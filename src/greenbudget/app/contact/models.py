from django.db import models

from happybudget.lib.django_utils.models import Choices
from happybudget.lib.utils import conditionally_separate_strings

from happybudget.app import model
from happybudget.app.io.utils import upload_user_image_to
from happybudget.app.tabling.models import OrderedRowModel

from .managers import ContactManager


def upload_to(instance, filename):
    return upload_user_image_to(
        user=instance.user_owner,
        filename=filename,
        directory="contacts"
    )


@model.model(type='contact')
class Contact(OrderedRowModel):
    first_name = models.CharField(max_length=30, null=True)
    last_name = models.CharField(max_length=30, null=True)
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
    notes = models.CharField(null=True, max_length=256)
    attachments = models.ManyToManyField(
        to='io.Attachment',
        related_name='contacts'
    )

    objects = ContactManager()
    table_pivot = ('created_by_id', )
    user_ownership_field = 'created_by'

    class Meta:
        get_latest_by = "order"
        ordering = ('order', )
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"
        unique_together = (('created_by', 'order'))

    def __str__(self):
        return self.email or self.full_name or ""

    @property
    def full_name(self):
        return conditionally_separate_strings([self.first_name, self.last_name])
