from phonenumber_field.serializerfields import PhoneNumberField

from rest_framework import serializers

from greenbudget.lib.rest_framework_utils.serializers import (
    EnhancedModelSerializer)

from .models import Contact


class ContactSerializer(EnhancedModelSerializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    full_name = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    role = serializers.ChoiceField(
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
            'first_name', 'last_name', 'created_at', 'updated_at', 'role',
            'city', 'country', 'phone_number', 'email', 'full_name')
