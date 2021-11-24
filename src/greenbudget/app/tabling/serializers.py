from copy import deepcopy

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

        original_validate = getattr(klass, 'validate')

        def validate(serializer, attrs):
            context = LazyContext(serializer, 'row_order_serializer')
            filter_data = self._table_filter(context)
            table = model_cls.objects.get_table(**filter_data)

            def get_bounds(previous):
                if previous is not None:
                    index = list(table).index(previous)
                    try:
                        next_instance = table[index + 1]
                    except IndexError:
                        next_instance = None
                else:
                    next_instance = table.first()
                return [previous, next_instance]

            validated = original_validate(serializer, attrs)
            if 'previous' in validated:
                previous = validated.pop('previous')
                bounds = get_bounds(previous)

                if serializer.instance is not None:
                    if previous == serializer.instance:
                        raise InvalidFieldError('previous', message=(
                            'Previous instance cannot be the instance being '
                            'updated.'
                        ))
                    # Check to make sure that the previous instance that the
                    # updating instance is being ordered relative to is not
                    # already the previous instance before the updating instance.
                    # If it is, no update is required.
                    current_index = list(table).index(serializer.instance)
                    current_previous = None
                    if current_index >= 1:
                        current_previous = table[current_index - 1]
                    if current_previous == bounds[0]:
                        return validated

                bounds = get_bounds(previous)
                if bounds[0] is None:
                    validated['order'] = lexographic_midpoint(
                        upper=bounds[1].order)
                elif bounds[1] is None:
                    validated['order'] = lexographic_midpoint(
                        lower=bounds[0].order)
                else:
                    validated['order'] = lexographic_midpoint(
                        lower=bounds[0].order,
                        upper=bounds[1].order
                    )
            return validated

        setattr(klass, 'validate', validate)

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
