from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from happybudget.app import exceptions
from happybudget.app.user.models import User


class CollaboratingUserField(serializers.PrimaryKeyRelatedField):
    @property
    def user(self):
        assert 'request' in self.context, \
            "The request must be provided in context when using this " \
            "serializer field."
        return self.context['request'].user

    @property
    def user_owner(self):
        assert 'budget' in self.context, \
            "The budget must be provided in context when using this " \
            "serializer field."
        return self.context['budget'].user_owner

    def get_queryset(self):
        assert self.user.is_fully_authenticated
        # We have to update the queryset of the collaborating user such that it
        # excludes the following users:
        # (1) The user submitting the request: Since a user cannot assign
        #     themselves as a collaborator.
        # (2) The user that created the instance: Since a user cannot be
        #     a collaborator of an instance that they are the owner of.
        return User.objects.fully_authenticated().exclude(
            pk__in=[self.user_owner.pk, self.user.pk])

    def to_internal_value(self, data):
        if self.pk_field is not None:
            data = self.pk_field.to_internal_value(data)
        queryset = self.get_queryset()
        try:
            if isinstance(data, bool):
                raise TypeError
            return queryset.get(pk=int(data))
        except ObjectDoesNotExist as e:
            if int(data) == self.user.pk:
                raise exceptions.ValidationError(
                    message=_(
                        'A user cannot assign themselves as a collaborator.'),
                    code='invalid'
                ) from e
            elif int(data) == self.user_owner.pk:
                raise exceptions.ValidationError(
                    message=_(
                        f'The user {data} created the instance and cannot be '
                        'assigned as a collaborator.'
                    ),
                    code='invalid'
                ) from e
            self.fail('does_not_exist', pk_value=data)
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)
