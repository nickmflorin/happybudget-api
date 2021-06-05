from model_utils import Choices

from django.db import models


class Contact(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30, null=True)
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
    role = models.IntegerField(choices=ROLES, null=True)
    city = models.CharField(max_length=30, null=True)
    country = models.CharField(max_length=30, null=True)
    phone_number = models.BigIntegerField(null=True)
    email = models.EmailField(null=True)

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
        if self.last_name is not None:
            return self.first_name + " " + self.last_name
        return self.first_name
