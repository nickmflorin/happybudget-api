from rest_framework import serializers

from greenbudget.lib.drf.fields import ModelChoiceField, Base64ImageField
from greenbudget.lib.drf.serializers import (
    ModelSerializer)

from .models import Contact


class ContactSerializer(ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    first_name = serializers.CharField(allow_null=True, required=False)
    last_name = serializers.CharField(allow_null=True, required=False)
    full_name = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    type = ModelChoiceField(
        required=False,
        choices=Contact.TYPES,
        allow_null=True
    )
    company = serializers.CharField(allow_null=True, required=False)
    position = serializers.CharField(allow_null=True, required=False)
    city = serializers.CharField(allow_null=True, required=False)
    phone_number = serializers.IntegerField(allow_null=True, required=False)
    email = serializers.EmailField(allow_null=True, required=False)
    rate = serializers.IntegerField(allow_null=True, required=False)
    image = Base64ImageField(required=False)

    class Meta:
        model = Contact
        fields = (
            'id', 'first_name', 'last_name', 'created_at', 'updated_at', 'type',
            'city', 'rate', 'phone_number', 'email', 'full_name', 'company',
            'position', 'image')
