from django.core.exceptions import FieldDoesNotExist
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from greenbudget.lib.drf.fields import find_field_original_serializer


class TableChildrenPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    default_error_messages = {
        'does_not_exist': _(
            'The child {child_instance_name} with ID {pk_value} either does '
            'not exist or does not belong to the same parent '
            '({parent_instance_name} with ID {parent_pk_value}) as the '
            '{obj_name}.'
        ),
    }

    def __init__(self, *args, **kwargs):
        self._obj_name = kwargs.pop('obj_name')
        self._child_instance_cls = kwargs.pop('child_instance_cls')
        self._additional_instance_query = kwargs.pop(
            'additional_instance_query', None)
        self._exclude_instance_query = kwargs.pop(
            'exclude_instance_query', None)

        self._error_message = kwargs.pop('error_message', None)
        super().__init__(*args, **kwargs)
        if self._error_message is not None:
            self.error_messages.update(does_not_exist=self._error_message)

    def _to_query(self, q, param):
        # In a POST request, there will not be an instance on the serializer.
        if self.request.method == "POST" or q is None:
            return models.Q()
        instance = self.parent.parent.instance
        if isinstance(q, models.Q):
            return q
        try:
            return q(self.parent_instance, instance)
        except TypeError:
            raise TypeError(
                "`%s` must either be a callable taking the parent instance "
                "and updating instance as it's only arguments, or a class type."
                % param
            )

    @property
    def parent_instance(self):
        if 'parent' not in self.context:
            raise Exception(
                "The `parent` must be provided in context when using this "
                "serializer field."
            )
        return self.context['parent']

    @property
    def request(self):
        if 'request' not in self.context:
            raise Exception(
                "The `request` must be provided in context when using this "
                "serializer field."
            )
        return self.context['request']

    @property
    def child_instance_cls(self):
        if isinstance(self._child_instance_cls, type):
            return self._child_instance_cls
        try:
            return self._child_instance_cls(self.parent_instance)
        except TypeError:
            raise TypeError(
                "`child_instance_cls` must either be a callable taking the "
                "parent instance as it's only argument or a class type."
            )

    @property
    def exclude_instance_query(self):
        return self._to_query(
            self._exclude_instance_query,
            'exclude_instance_query'
        )

    @property
    def additional_instance_query(self):
        return self._to_query(
            self._additional_instance_query,
            'additional_instance_query'
        )

    @property
    def parent_query(self):
        child_instance_cls = self.child_instance_cls
        try:
            parent_field = child_instance_cls._meta.get_field('parent')
        except FieldDoesNotExist:
            raise Exception(
                "The model %s must have a `parent` field in order to be "
                "associated with a Group instance."
                % child_instance_cls.__name__
            )
        q = models.Q(parent=self.parent_instance)
        if isinstance(parent_field, GenericForeignKey):
            q = models.Q(
                content_type=ContentType.objects.get_for_model(
                    type(self.parent_instance)),
                object_id=self.parent_instance.pk
            )
        return q

    def fail(self, key, **kwargs):
        if key != 'does_not_exist':
            super().fail(key, **kwargs)
        # Update the default error messages to include more information if the
        # child does not exist in the queryset limited by the parent.
        super().fail(
            key=key,
            parent_pk_value=self.parent_instance.pk,
            obj_name=self._obj_name.lower(),
            child_instance_name=getattr(
                self.child_instance_cls._meta,
                "verbose_name",
                "instance"
            ).lower(),
            parent_instance_name=getattr(
                type(self.parent_instance)._meta,
                "verbose_name",
                "object being updated"
            ).lower(),
            **kwargs
        )

    def get_queryset(self):
        child_instance_cls = self.child_instance_cls
        return child_instance_cls.objects \
            .filter(self.parent_query & self.additional_instance_query) \
            .exclude(self.exclude_instance_query)


class BudgetFilteredQuerysetPKField(serializers.PrimaryKeyRelatedField):
    default_error_messages = {
        **serializers.PrimaryKeyRelatedField.default_error_messages,
        ** {
            'does_not_exist': _(
                'The instance "{pk_value}" does not belong to the correct '
                'budget.'
            ),
        }
    }

    def __init__(self, *args, **kwargs):
        self._apply_filter = kwargs.pop('apply_filter', None)
        self._budget_getter = kwargs.pop('budget_getter', None)
        self._object_name = kwargs.pop('object_name', None)
        if self._object_name is not None:
            self.default_error_messages['does_not_exist'] = _(
                'The %s "{pk_value}" does not belong to the correct '
                'budget.' % self._object_name
            )
        self._budget_field = kwargs.pop('budget_field', 'budget')
        super().__init__(*args, **kwargs)

    def get_queryset(self, budget=None):
        qs = super().get_queryset()

        original_serializer = find_field_original_serializer(self)
        if original_serializer is None:
            raise Exception("Invalid use of %s." % self.__class__.__name__)

        # We allow the budget to be explicitly passed in for serializer fields
        # that extend this one.
        if budget is None:
            if self._budget_getter is not None:
                budget = self._budget_getter(original_serializer)
            else:
                budget = original_serializer.context.get('budget')
                if budget is None:
                    if original_serializer.instance is None:
                        raise Exception(
                            "The budget must be provided in context when using "
                            "the serializer %s in an update context."
                            % original_serializer.__class__.__name__
                        )
                    budget = getattr(original_serializer.instance,
                                    self._budget_field)

        if budget is None:
            raise Exception("The budget must be present to use this field.")

        if self._apply_filter is not None:
            return self._apply_filter(qs, budget)

        filter_kwargs = {self._budget_field: budget}
        return qs.filter(**filter_kwargs)
