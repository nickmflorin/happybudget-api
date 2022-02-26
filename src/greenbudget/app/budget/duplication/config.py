from django.db import models

from greenbudget.lib.django_utils.models import ModelMap
from .fields import DisallowedField, AllowedFieldOverride


DT_FIELDS = (models.fields.DateTimeField, models.fields.DateField)


DISALLOWED_FIELDS = [
    DisallowedField(attribute=[('editable', False), ('primary_key', True)]),
    DisallowedField(name=('id', 'object_id')),
    DisallowedField(cls=[
        models.fields.AutoField,
        models.ManyToManyField,
        models.ForeignKey,
        models.OneToOneField,
        models.ImageField,
        models.FileField,
    ]),
    DisallowedField(
        conditional={
            'cls': DT_FIELDS,
            'disallowed': lambda field: field.auto_now_add is True
            or field.auto_now is True
        }
    )
]


ALLOW_FIELD_OVERRIDES = ModelMap({
    'group.Group': AllowedFieldOverride(name='color', cls=models.ForeignKey),
    'actual.Actual': AllowedFieldOverride(
        name='contact',
        cls=models.ForeignKey,
        conditional=lambda value, user: value is None or value.created_by == user
    ),
    'subaccount.SubAccount': [
        AllowedFieldOverride(
            name='contact',
            cls=models.ForeignKey,
            conditional=lambda value, user: value is None
            or value.created_by == user
        ),
        AllowedFieldOverride(name='unit', cls=models.ForeignKey)
    ]
})
