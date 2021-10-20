from rest_framework import serializers

from greenbudget.lib.drf.fields import Base64ImageField

from .models import HeaderTemplate


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


class HeaderTemplateSerializer(SimpleHeaderTemplateSerializer):
    left_image = Base64ImageField(required=False, allow_null=True)
    right_image = Base64ImageField(required=False, allow_null=True)
    left_info = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True
    )
    right_info = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True
    )
    header = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True
    )
    original = serializers.PrimaryKeyRelatedField(
        write_only=True,
        queryset=HeaderTemplate.objects.all(),
        required=False
    )

    class Meta:
        model = HeaderTemplate
        fields = SimpleHeaderTemplateSerializer.Meta.fields + (
            'left_image', 'right_image', 'left_info', 'right_info', 'header',
            'original')

    def validate_left_info(self, value):
        if value is None or value.strip() == "":
            return None
        return value.strip()

    def validate_right_info(self, value):
        if value is None or value.strip() == "":
            return None
        return value.strip()

    def validate_header(self, value):
        if value is None or value.strip() == "":
            return None
        return value.strip()

    def validate(self, attrs):
        attrs = super().validate(attrs)
        original = attrs.pop('original', None)
        if original is not None:
            attrs.setdefault('header', original.left_info)
            attrs.setdefault('left_info', original.left_info)
            attrs.setdefault('right_info', original.right_info)
            attrs.setdefault('left_image', original.left_image)
            attrs.setdefault('right_image', original.right_image)
        return attrs
