from rest_framework import serializers

from happybudget.lib.drf.fields import ModelChoiceField

from happybudget.app.io.fields import Base64ImageField
from happybudget.app.io.serializers import SimpleAttachmentSerializer
from happybudget.app.io.models import Attachment
from happybudget.app.serializers import ModelSerializer
from happybudget.app.tabling.serializers import row_order_serializer

from .models import Contact


class ContactSerializer(ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    type = serializers.CharField(read_only=True)
    order = serializers.CharField(read_only=True)
    first_name = serializers.CharField(allow_null=True, required=False)
    last_name = serializers.CharField(allow_null=True, required=False)
    full_name = serializers.CharField(read_only=True)
    contact_type = ModelChoiceField(
        required=False,
        choices=Contact.TYPES,
        allow_null=True
    )
    company = serializers.CharField(allow_null=True, required=False)
    position = serializers.CharField(allow_null=True, required=False)
    city = serializers.CharField(allow_null=True, required=False)
    phone_number = serializers.CharField(allow_null=True, required=False)
    email = serializers.EmailField(allow_null=True, required=False)
    rate = serializers.IntegerField(allow_null=True, required=False)
    image = Base64ImageField(required=False, allow_null=True)
    order = serializers.CharField(read_only=True)
    notes = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=True,
        trim_whitespace=False
    )
    attachments = serializers.PrimaryKeyRelatedField(
        queryset=Attachment.objects.all(),
        required=False,
        many=True
    )

    class Meta:
        model = Contact
        fields = (
            'id', 'first_name', 'last_name', 'type', 'city', 'rate',
            'phone_number', 'email', 'full_name', 'company', 'position',
            'image', 'contact_type', 'attachments', 'order', 'notes')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.update(attachments=SimpleAttachmentSerializer(
            instance=instance.attachments.all(),
            many=True
        ).data)
        return data


@row_order_serializer(table_filter=lambda d: {'created_by_id': d.user.id})
class ContactDetailSerializer(ContactSerializer):
    pass
