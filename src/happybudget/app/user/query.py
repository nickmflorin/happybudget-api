from django.db import models
from django.db.models.functions import Concat

from .mixins import ModelOwnershipMixin


class UserQuerySetMixin:
    def annotate_name(self):
        """
        Annotates the :obj:`QuerySet` class for models that have `first_name`
        and `last_name` fields such that model instances can be queried by
        a more general `name` parameter (which looks at both the first and last
        names).
        """
        return self.annotate(name=models.Case(
            models.When(
                first_name=None,
                last_name=None,
                then=models.Value(None)
            ),
            models.When(
                first_name=None,
                then=models.F('last_name')
            ),
            models.When(
                last_name=None,
                then=models.F('first_name')
            ),
            default=Concat(
                models.F('first_name'),
                models.Value(' '),
                models.F('last_name'),
                output_field=models.CharField()
            )
        ))


class UserQuerier(UserQuerySetMixin):
    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)

    def verified(self):
        return self.filter(is_verified=True)

    def unverified(self):
        return self.filter(is_verified=False)

    def fully_authenticated(self):
        return self.active().verified()


class UserQuerySet(UserQuerier, models.query.QuerySet):
    pass


class ModelOwnershipQuerier:
    def owned_by(self, user, strict=True):
        assert issubclass(self.model, ModelOwnershipMixin), \
            f"The model {self.model.__name__} does not dictate ownership."
        supported = self.model.raise_owner_db_lookup_not_supported(
            raise_exception=strict)
        if supported:
            query_kwargs = {self.model.user_ownership_field: user}
            return self.filter(**query_kwargs)
        # If the queryset filter lookup is not supported, this means that the
        # user ownership field at some level points to a model attribute instead
        # of a model field.  In this case, we have to filter the queryset in
        # native Python.
        instances = [m for m in self.all() if m.user_owner == user]
        return self.filter(pk__in=[m.pk for m in instances])
