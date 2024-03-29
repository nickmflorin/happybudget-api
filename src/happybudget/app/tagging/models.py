from colorful.fields import RGBColorField
from polymorphic.models import PolymorphicModel

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.contrib.contenttypes.models import ContentType
from django.db import models, IntegrityError

from .managers import ColorManager


ColorCodeValidator = RegexValidator(
    r'^#(?:[0-9a-fA-F]{3}){1,2}$',
    message="Enter a valid color hexadecimal code."
)


class Color(models.Model):
    code = RGBColorField(
        unique=True,
        validators=[ColorCodeValidator],
    )
    name = models.CharField(max_length=32, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    content_types = models.ManyToManyField(
        to=ContentType,
        blank=True,
        limit_choices_to=models.Q(app_label='group', model='group')
        | models.Q(app_label='fringe', model='fringe')
        | models.Q(app_label='subaccount', model='subaccountunit')
        | models.Q(app_label='actual', model='actualtype')
    )

    objects = ColorManager()

    class Meta:
        get_latest_by = "created_at"
        ordering = ('created_at', )
        verbose_name = "Color"
        verbose_name_plural = "Colors"
        constraints = [
            models.CheckConstraint(
                check=models.Q(code__startswith='#'),
                name="%(app_label)s_%(class)s_valid_hex_code",
            )
        ]

    def __str__(self):
        return "{name}: {code}".format(
            name=self.name,
            code=self.code
        )

    def save(self, **kwargs):
        try:
            self.full_clean()
        except ValidationError as e:
            raise IntegrityError(str(e)) from e
        return super().save(**kwargs)


class Tag(PolymorphicModel):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=32)
    plural_title = models.CharField(max_length=32, null=True, blank=True)
    order = models.IntegerField(null=True)

    class Meta:
        get_latest_by = "created_at"
        ordering = ("created_at",)
        verbose_name = "Tag"
        verbose_name_plural = "All Tags"
        unique_together = (('title', 'polymorphic_ctype_id'))

    def __str__(self):
        return "<Tag title={title} order={order}>".format(
            title=self.title,
            order=self.order
        )

    def validate_before_save(self):
        if self.order is None:
            instances = Tag.objects \
                .filter(polymorphic_ctype_id=self.polymorphic_ctype_id) \
                .order_by('order', '-updated_at') \
                .only('order').exclude(pk=self.pk)
            if instances.count():
                self.order = max([i.order for i in instances]) + 1
            else:
                self.order = 0

    def save(self, *args, **kwargs):
        setattr(self, '_ignore_reindex', kwargs.pop('ignore_reindex', False))
        super().save(*args, **kwargs)
