from copy import deepcopy

from django.db import transaction

from greenbudget.lib.drf.exceptions import InvalidFieldError
from greenbudget.lib.drf.serializers import LazyContext

from .fields import TablePrimaryKeyRelatedField
from .utils import lexographic_midpoint


class row_order_serializer:
    """
    A decorator that configures a :obj:`serializers.ModelSerializer` class
    such that it can accept a `previous` parameter, update or create the
    associated model in the table with the proper ordering.

    Due to the complexities and inheritance patterns of most of our serializers
    related to tabular data, incorporating this behavior via inheritance is not
    possible or clean, so this decorator should be used instead.

    Race Conditions in Regard to Ordering
    -------------------------------------
    When creating a new instance and a default order is required, we need to
    look at the current ordering of the other instances that comprise the same
    table subset in the database.  If we are not careful, race conditions can
    cause conflictings values for `order` as the time between when the ordering
    of the existing table subset is evaluated and when the new instance is saved
    is not negligible.  In order to avoid this, we use transaction locks on rows
    that correspond to other instances of the same table subset when defaulting
    the order of a newly created row.

    While this logic is also applied in the pre-save signals for the relevant
    models, that logic should be relied on more as a fallback for when instances
    are manually updated or created via management commands or shell commands.
    This is because we cannot lock the rows for the entire time between when
    the pre-save signal is triggered and when the instance is saved - so it will
    be more prone to race condition conflicts during HTTP requests than if we
    were to apply the logic here as well.
    """

    def __init__(self, table_filter):
        self._table_filter = table_filter

    def __call__(self, cls):
        klass = deepcopy(cls)

        # This is necessary so we do not mutate the Meta fields of any
        # serializers the serializer this decorator decorates inherits from.
        class Meta(klass.Meta):
            fields = klass.Meta.fields + ('previous', )

        setattr(klass, 'Meta', Meta)
        model_cls = klass.Meta.model

        original_create = getattr(klass, 'create')
        original_update = getattr(klass, 'update')

        def get_instance_bounds(table, previous):
            if previous is not None:
                index = list(table).index(previous)
                try:
                    next_instance = table[index + 1]
                except IndexError:
                    next_instance = None
            else:
                next_instance = table.first()
            return [previous, next_instance]

        def get_relative_order(table, previous):
            bounds = get_instance_bounds(table, previous)
            if bounds[0] is None:
                return lexographic_midpoint(upper=bounds[1].order)
            elif bounds[1] is None:
                return lexographic_midpoint(lower=bounds[0].order)
            else:
                return lexographic_midpoint(
                    lower=bounds[0].order,
                    upper=bounds[1].order
                )

        @transaction.atomic
        def create(serializer, validated_data):
            """
            Overrides the traditional `ModelSerializer.create` method such that
            the rows corresponding to the table subset of instances are locked
            during the transaction to avoid conflicting values of the `order`
            field due to race conditions.
            """
            # Lock the rows corresponding to other instances in the table
            # subset such that two requests to create an instance at the
            # same time do not result in conflicting orders for the new
            # instance.
            context = LazyContext(serializer)
            table = model_cls.get_table(
                self._table_filter(context)).select_for_update()

            # When creating instances, either the `prevous` instance is included
            # in the request data or the order is defaulted to the end of the
            # table.
            if 'previous' in validated_data:
                previous = validated_data.pop('previous')
                validated_data['order'] = get_relative_order(table, previous)
            else:
                try:
                    last_in_table = table.latest()
                except model_cls.DoesNotExist:
                    validated_data['order'] = lexographic_midpoint()
                else:
                    validated_data['order'] = lexographic_midpoint(
                        lower=last_in_table.order)
            return original_create(serializer, validated_data)

        @transaction.atomic
        def update(serializer, instance, validated_data):
            """
            Overrides the traditional `ModelSerializer.update` method such that
            the rows corresponding to the table subset of instances are locked
            during the transaction to avoid conflicting values of the `order`
            field due to race conditions.
            """
            if 'previous' in validated_data:
                previous = validated_data.pop('previous')
                if previous == instance:
                    raise InvalidFieldError('previous', message=(
                        'Previous instance cannot be the instance being '
                        'updated.'
                    ))
                # Lock the rows corresponding to other instances in the table
                # subset such that two requests to create an instance at the
                # same time do not result in conflicting orders for the new
                # instance.
                context = LazyContext(serializer)
                table = model_cls.get_table(
                    self._table_filter(context)).select_for_update()
                bounds = get_instance_bounds(table, previous)

                # Check to make sure that the previous instance that the
                # updating instance is being ordered relative to is not
                # already the previous instance before the updating instance.
                # If it is, no update is required.
                current_index = list(table).index(instance)
                current_previous = None
                if current_index >= 1:
                    current_previous = table[current_index - 1]
                if current_previous != bounds[0]:
                    validated_data['order'] = get_relative_order(table, previous)
            return original_update(serializer, instance, validated_data)

        setattr(klass, 'create', create)
        setattr(klass, 'update', update)

        previous_field = TablePrimaryKeyRelatedField(
            required=False,
            allow_null=True,
            write_only=True,
            table_filter=self._table_filter
        )
        setattr(klass, 'previous', previous_field)
        # This is because there is some meta programming around DRF's serializer.
        klass._declared_fields['previous'] = previous_field
        return klass
