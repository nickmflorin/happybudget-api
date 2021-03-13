from model_utils import Choices
from phonenumber_field.modelfields import PhoneNumberField

from django.db import models


class Contact(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(
        to='user.User',
        on_delete=models.CASCADE,
        related_name="contacts"
    )
    ROLES = Choices(
        (0, "producer", "Producer"),
        (1, "executive_producer", "Executive Producer"),
        (2, "production_manager", "Production Manager"),
        (3, "production_designer", "Production Designer"),
        (4, "actor", "Actor"),
        (5, "director", "Director"),
        (6, "medic", "Medic"),
        (7, "wardrobe", "Wardrobe"),
        (8, "writer", "Writer"),
        (9, "client", "Client"),
        (10, "other", "Other"),
    )
    role = models.IntegerField(choices=ROLES)
    # TODO: Use a better system for establishing contact location.
    city = models.CharField(max_length=30)
    country = models.CharField(max_length=30)
    phone_number = PhoneNumberField()
    email = models.EmailField()

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
        return self.first_name + " " + self.last_name
