from model_utils import Choices

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Actual(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        to='user.User',
        related_name='created_actuals',
        on_delete=models.SET_NULL,
        null=True
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        to='user.User',
        related_name='updated_actuals',
        on_delete=models.SET_NULL,
        null=True
    )
    description = models.CharField(null=True, max_length=128)
    vendor = models.CharField(null=True, max_length=128)
    purchase_order = models.CharField(null=True, max_length=128)
    date = models.DateTimeField(null=True)
    payment_id = models.CharField(max_length=50, null=True)
    value = models.DecimalField(decimal_places=2, max_digits=10, null=True)
    PAYMENT_METHODS = Choices(
        (0, "check", "Check"),
        (1, "card", "Card"),
        (2, "wire", "Wire"),
    )
    payment_method = models.IntegerField(choices=PAYMENT_METHODS, null=True)

    content_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.CASCADE,
        limit_choices_to=models.Q(app_label='account', model='Account')
        | models.Q(app_label='subaccount', model='SubAccount')
    )
    object_id = models.PositiveIntegerField()
    parent = GenericForeignKey('content_type', 'object_id')

    class Meta:
        get_latest_by = "updated_at"
        # Since the data from this model is used to power AGGridReact tables,
        # we want to keep the ordering of the accounts consistent.
        ordering = ('created_at', )
        verbose_name = "Actual"
        verbose_name_plural = "Actual"

    def __str__(self):
        return "<{cls} id={id}, value={value}, content_type={content_type}>".format(  # noqa
            cls=self.__class__.__name__,
            id=self.pk,
            content_type=self.content_type.model,
            value=self.value,
        )

    @property
    def payment_method_name(self):
        if self.payment_method is None:
            return ""
        return self.PAYMENT_METHODS[self.payment_method]
