from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation)
from django.contrib.contenttypes.models import ContentType
from django.db.utils import IntegrityError
from polymorphic.models import PolymorphicModel

from django.core.validators import (
    MaxValueValidator, MinValueValidator, MinLengthValidator)
from django.db import models

from greenbudget.app import signals
from greenbudget.app.user.utils import upload_user_image_to


def upload_to(instance, filename):
    return upload_user_image_to(
        user=instance.created_by,
        filename=filename,
        directory="exports/templates"
    )


FLAG_TO_STYLE_MAP = {
    'is_bold': 'bold',
    'is_italic': 'italic'
}


class TextDataElement(PolymorphicModel):
    content_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.CASCADE,
        limit_choices_to=models.Q(app_label='pdf', model='TextGroup')
        | models.Q(app_label='pdf', model='Block')
    )
    object_id = models.PositiveIntegerField(db_index=True)
    parent = GenericForeignKey('content_type', 'object_id')

    def save(self, *args, **kwargs):
        force_alteration = kwargs.pop('force_alteration', False)
        if self.id is not None and not force_alteration:
            raise IntegrityError(
                "Model {cls} cannot be altered after it was created.".format(
                    cls=self.__class__.__name__))
        return super().save(*args, **kwargs)


class TextFragmentGroup(TextDataElement):
    data = GenericRelation(TextDataElement)

    class Meta:
        verbose_name = "Text Group"
        verbose_name_plural = "Text Groups"

    def save(self, *args, **kwargs):
        force_alteration = kwargs.pop('force_alteration', False)
        if self.id is not None and not force_alteration:
            raise IntegrityError(
                "Model {cls} cannot be altered after it was created.".format(
                    cls=self.__class__.__name__))
        return super().save(*args, **kwargs)


class TextFragment(TextDataElement):
    text = models.CharField(max_length=256)
    is_bold = models.BooleanField(default=False)
    is_italic = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Text Fragment"
        verbose_name_plural = "Text Fragments"

    @property
    def styles(self):
        styles = [
            v
            for k, v in FLAG_TO_STYLE_MAP.items()
            if getattr(self, k) is True
        ]
        return styles or None

    def __str__(self):
        return "<{cls} text={text} styles={styles}>".format(
            cls=self.__class__.__name__,
            text=self.text,
            styles=self.styles
        )

    def save(self, *args, **kwargs):
        force_alteration = kwargs.pop('force_alteration', False)
        if self.id is not None and not force_alteration:
            raise IntegrityError(
                "Model {cls} cannot be altered after it was created.".format(
                    cls=self.__class__.__name__))
        return super().save(*args, **kwargs)


class Block(PolymorphicModel):
    data = GenericRelation(TextDataElement)
    field = models.ForeignKey(
        to='pdf.ExportField',
        on_delete=models.CASCADE,
        related_name='blocks'
    )

    def save(self, *args, **kwargs):
        force_alteration = kwargs.pop('force_alteration', False)
        if self.id is not None and not force_alteration:
            raise IntegrityError(
                "Model {cls} cannot be altered after it was created.".format(
                    cls=self.__class__.__name__))
        return super().save(*args, **kwargs)


class HeadingBlock(Block):
    type = "header"
    level = models.IntegerField(
        default=2,
        validators=[
            MaxValueValidator(6),
            MinValueValidator(1)
        ]
    )

    def __str__(self):
        return "<Block type={type}>".format(type=self.type)

    def save(self, *args, **kwargs):
        force_alteration = kwargs.pop('force_alteration', False)
        if self.id is not None and not force_alteration:
            raise IntegrityError(
                "Model {cls} cannot be altered after it was created.".format(
                    cls=self.__class__.__name__))
        return super().save(*args, **kwargs)


class ParagraphBlock(Block):
    type = "paragraph"

    class Meta:
        verbose_name = "Export Field"
        verbose_name_plural = "Export Fields"

    def __str__(self):
        return "<Block type={type}>".format(type=self.type)

    def save(self, *args, **kwargs):
        force_alteration = kwargs.pop('force_alteration', False)
        if self.id is not None and not force_alteration:
            raise IntegrityError(
                "Model {cls} cannot be altered after it was created.".format(
                    cls=self.__class__.__name__))
        return super().save(*args, **kwargs)


class ExportField(models.Model):
    class Meta:
        verbose_name = "Export Field"
        verbose_name_plural = "Export Fields"

    def save(self, *args, **kwargs):
        force_alteration = kwargs.pop('force_alteration', False)
        if self.id is not None and not force_alteration:
            raise IntegrityError(
                "Model {cls} cannot be altered after it was created.".format(
                    cls=self.__class__.__name__))
        return super().save(*args, **kwargs)


@signals.model(
    user_field='created_by',
    exclude_fields=[
        'created_by', 'created_at', 'updated_at', 'left_image', 'right_image']
)
class HeaderTemplate(models.Model):
    name = models.CharField(
        max_length=32,
        blank=False,
        validators=[MinLengthValidator(1)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        to='user.User',
        on_delete=models.CASCADE,
        related_name="header_templates"
    )
    header = models.OneToOneField(
        to='pdf.ExportField',
        on_delete=models.SET_NULL,
        null=True,
        related_name='header_template_header'
    )
    left_image = models.ImageField(upload_to=upload_to, null=True)
    left_info = models.OneToOneField(
        to='pdf.ExportField',
        on_delete=models.SET_NULL,
        null=True,
        related_name='header_template_left_info'
    )
    right_image = models.ImageField(upload_to=upload_to, null=True)
    right_info = models.OneToOneField(
        to='pdf.ExportField',
        on_delete=models.SET_NULL,
        null=True,
        related_name='header_template_right_info'
    )
    RICH_TEXT_FIELDS = ["header", "left_info", "right_info"]

    class Meta:
        verbose_name = "Header Template"
        verbose_name_plural = "Header Templates"
        unique_together = (('created_by', 'name'))

    def __str__(self):
        return "<{cls} created_by={created_by}>".format(
            cls=self.__class__.__name__,
            created_by=self.created_by_id,
        )
