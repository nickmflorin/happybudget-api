from phonenumber_field.serializerfields import PhoneNumberField

from rest_framework import serializers

from greenbudget.lib.rest_framework_utils.fields import ModelChoiceField
from greenbudget.lib.rest_framework_utils.serializers import (
    EnhancedModelSerializer)

from .models import Contact


class ContactSerializer(EnhancedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    full_name = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    role = ModelChoiceField(
        required=False,
        choices=Contact.ROLES
    )
    city = serializers.CharField()
    country = serializers.CharField()
    phone_number = PhoneNumberField()
    email = serializers.EmailField()

    class Meta:
        model = Contact
        fields = (
            'id', 'first_name', 'last_name', 'created_at', 'updated_at', 'role',
            'city', 'country', 'phone_number', 'email', 'full_name')

    def validate_email(self, value):
        user = self.context['user']
        validator = serializers.UniqueTogetherValidator(
            queryset=Contact.objects.filter(user=user),
            fields=('email', ),
        )
        validator({'email': value}, self)
        return value

    def validate_phone_number(self, value):
        user = self.context['user']
        validator = serializers.UniqueTogetherValidator(
            queryset=Contact.objects.filter(user=user),
            fields=('phone_number', ),
        )
        validator({'phone_number': value}, self)
        return value
