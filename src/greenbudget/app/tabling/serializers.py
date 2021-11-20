from rest_framework import serializers


class row_order_serializer:
    """
    A decorator that configures a :obj:`serializers.ModelSerializer` class
    such that it can accept an `order` parameter, update or create the
    associated model in the table with the proper ordering, and include the
    lexographic `order` parameter in the response.

    Due to the complexities and inheritance patterns of most of our serializers
    related to tabular data, incorporating this behavior via inheritance is not
    possible or clean, so this decorator should be used instead.
    """
    order = serializers.IntegerField(
        write_only=True,
        required=False,
        allow_null=False
    )

    def __init__(self, table_filter):
        self._table_filter = table_filter

    def __call__(self, cls):
        model_cls = cls.Meta.model
        cls.Meta.fields = cls.Meta.fields + ('order', )

        original_create = getattr(cls, 'create')
        original_update = getattr(cls, 'update')
        original_to_representation = getattr(cls, 'to_representation')

        def create(serializer, validated_data):
            if 'order' in validated_data:
                # The table filter keyword arguments are guaranteed to be in
                # the validated data because they will always be required when
                # creating an instance.  If they are not, it is a developer
                # error.
                filter_data = self._table_filter(validated_data)
                table = model_cls.objects.get_table(**filter_data)
                validated_data['order'] = table.get_order_at_integer(
                    validated_data.pop('order'),
                    # When inserting a new row in a table at a specific order,
                    # this direction causes the row to be inserted at the
                    # correct location.
                    direction='up'
                )
            return original_create(serializer, validated_data)

        def to_representation(serializer, instance):
            # Because we accept the `order` field as an integer ordering in the
            # table, and we need to include the `order` field in the response
            # as it's lexographic ordering, we have to set `write_only` on the
            # ordering IntegerField and override the response representation
            # here.
            data = original_to_representation(serializer, instance)
            data.update(order=instance.order)
            return data

        def update(serializer, instance, validated_data):
            if 'order' in validated_data:
                instance.order_at_integer(validated_data.pop('order'))
            return original_update(serializer, instance, validated_data)

        setattr(cls, 'update', update)
        setattr(cls, 'create', create)
        setattr(cls, 'to_representation', to_representation)
        setattr(cls, 'order', self.order)
        # This is because there is some meta programming around DRF's serializer.
        cls._declared_fields['order'] = self.order
        return cls
