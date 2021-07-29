from rest_framework import serializers
from rest_framework.fields import empty
from rest_polymorphic.serializers import PolymorphicSerializer

from greenbudget.lib.drf.fields import Base64ImageField

from .models import (
    TextFragment, HeaderTemplate, HeadingBlock, ParagraphBlock, ExportField,
    TextFragmentGroup)


class RecursiveBlocksSerializerField(serializers.ListField):
    def to_representation(self, instance):
        return TextFragmentSerializer(
            instance.all(), many=True).data


class TextFragmentGroupSerializer(serializers.ModelSerializer):
    data = RecursiveBlocksSerializerField(required=False, allow_empty=False)

    class Meta:
        model = TextFragmentGroup
        fields = ('data', )

    def create(self, validated_data):
        data = validated_data.pop('data')
        instance = super().create(validated_data)
        for data_element in data:
            serializer = PolymorphicTextDataElementSerializer(data=data_element)
            serializer.is_valid(raise_exception=True)
            serializer.save(group=instance)
        return instance


class TextFragmentSerializer(serializers.ModelSerializer):
    """
    A :obj:`rest_framework.serializers.ModelSerializer` class for the
    :obj:`TextFragment` model.

    This :obj:`rest_framework.serializers.ModelSerializer` will only ever
    be used in the create context, because we do not modify instances of
    :obj:`TextFragment`, we create and delete them.
    """
    styles = serializers.MultipleChoiceField(
        choices=["bold", "italic"],
        required=False,
    )
    text = serializers.CharField(
        required=True,
        allow_null=False,
        allow_blank=False
    )

    class Meta:
        model = TextFragment
        fields = ('styles', 'text')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data['styles'] is None:
            del data['styles']
        return data

    def to_internal_value(self, data):
        styles = data.pop('styles', [])
        data = super().to_internal_value(data)
        if 'is_bold' not in data and 'is_italic' not in data:
            data.update(
                is_bold='bold' in styles,
                is_italic='italic' in styles
            )
        return data


class PolymorphicTextDataElementSerializer(PolymorphicSerializer):
    model_serializer_mapping = {
        TextFragment: TextFragmentSerializer,
        TextFragmentGroup: TextFragmentGroupSerializer
    }

    def run_validation(self, data=empty):
        # Overridden so we do not need to include a resource_type parameter
        # in the request data.
        serializer = self._get_serializer_from_mapping(data)
        validated_data = serializer.run_validation(data)
        return validated_data

    def _get_resource_type_from_mapping(self, mapping):
        if "data" not in mapping and "text" not in mapping:
            raise serializers.ValidationError(
                "Could not infer text block type from provided data.")
        if "data" in mapping:
            return TextFragmentGroup
        return TextFragment

    def _get_serializer_from_mapping(self, mapping):
        # Overridden so we do not need to include a resource_type parameter
        # in the request data.
        model_cls = self._get_resource_type_from_mapping(mapping)
        return self._get_serializer_from_model_or_instance(model_cls)

    def to_representation(self, instance):
        # Overridden so we do not need to include a resource_type parameter
        # in the request data.
        serializer = self._get_serializer_from_model_or_instance(instance)
        ret = serializer.to_representation(instance)
        return ret

    def to_internal_value(self, data):
        # Overridden so we do not need to include a resource_type parameter
        # in the request data.
        serializer = self._get_serializer_from_mapping(data)
        return serializer.to_internal_value(data)

    def create(self, validated_data):
        # Overridden so we do not need to include a resource_type parameter
        # in the request data.
        serializer = self._get_serializer_from_mapping(validated_data)
        return serializer.create(validated_data)


class BlockSerializer(serializers.ModelSerializer):
    data = PolymorphicTextDataElementSerializer(many=True)

    class Meta:
        abstract = True
        fields = ('data', )

    def create(self, validated_data):
        data = validated_data.pop('data')
        instance = super().create(validated_data)
        create_data = [{**v, **{'parent': instance}} for v in data]
        serializer = PolymorphicTextDataElementSerializer(many=True)
        # This might not be totally necessary because we have
        # ATOMIC_REQUESTS on, but just in case.
        try:
            serializer.create(create_data)
        except Exception as e:
            instance.delete()
            raise e
        return instance


class HeadingBlockSerializer(BlockSerializer):
    level = serializers.IntegerField(min_value=1, max_value=6)

    class Meta:
        model = HeadingBlock
        fields = BlockSerializer.Meta.fields + ('level', )


class ParagraphBlockSerializer(BlockSerializer):
    class Meta:
        model = ParagraphBlock
        fields = BlockSerializer.Meta.fields


class PolymorphicBlockSerializer(PolymorphicSerializer):
    resource_type_field_name = 'type'
    model_serializer_mapping = {
        HeadingBlock: HeadingBlockSerializer,
        ParagraphBlock: ParagraphBlockSerializer
    }

    def to_resource_type(self, model_or_instance):
        return model_or_instance.type

    def create(self, validated_data):
        block_type = validated_data.pop('type')
        serializer = self._get_serializer_from_resource_type(block_type)
        return serializer.create(validated_data)


class ExportFieldField(serializers.ListField):
    def __init__(self, *args, **kwargs):
        kwargs['child'] = PolymorphicBlockSerializer()
        super().__init__(*args, **kwargs)

    def to_representation(self, instance):
        return PolymorphicBlockSerializer(instance.blocks.all(), many=True).data

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        if len(data) == 0:
            return None
        return data


class SimpleHeaderTemplateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(
        required=True, allow_null=False, allow_blank=False)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = HeaderTemplate
        fields = ('id', 'created_at', 'updated_at', 'name')

    def validate_name(self, value):
        user = self.context['user']
        validator = serializers.UniqueTogetherValidator(
            queryset=HeaderTemplate.objects.filter(created_by=user),
            fields=('name', ),
        )
        validator({'name': value, 'created_by': user}, self)
        return value


EXPORT_FIELDS = ['left_info', 'right_info', 'header']


class HeaderTemplateSerializer(SimpleHeaderTemplateSerializer):
    left_image = Base64ImageField(required=False, allow_null=True)
    right_image = Base64ImageField(required=False, allow_null=True)
    left_info = ExportFieldField(required=False)
    right_info = ExportFieldField(required=False)
    header = ExportFieldField(required=False)

    class Meta:
        model = HeaderTemplate
        fields = SimpleHeaderTemplateSerializer.Meta.fields + (
            'left_image', 'right_image', 'left_info', 'right_info', 'header')

    def reestablish_export_field(self, field, blocks_data, instance=None):
        # If the block data was an empty array, or None, we do not want to
        # create another ExportField.  The current ExportField will be deleted
        # after the HeaderTemplate is saved (due to the signals).
        if blocks_data is None:
            return None

        new_field = ExportField.objects.create()
        serializer = PolymorphicBlockSerializer(many=True)
        create_data = [{**v, **{'field': new_field}} for v in blocks_data]
        # This might not be totally necessary because we have
        # ATOMIC_REQUESTS on, but just in case.
        try:
            serializer.create(create_data)
        except Exception as e:
            new_field.delete()
            raise e

        return new_field

    def reestablish_export_fields(self, validated_data, instance=None):
        for field in EXPORT_FIELDS:
            if field in validated_data:
                block_data = validated_data.pop(field)
                validated_data[field] = self.reestablish_export_field(
                    field, block_data, instance=instance)
        return validated_data

    def update(self, instance, validated_data):
        validated_data = self.reestablish_export_fields(
            validated_data, instance=instance)
        return super().update(instance, validated_data)

    def create(self, validated_data):
        validated_data = self.reestablish_export_fields(validated_data)
        return super().create(validated_data)
