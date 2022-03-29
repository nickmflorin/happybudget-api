from django.db import models
from django.db.models.functions import Concat


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

    def standard_filter(self):
        return self.active().verified()


class UserQuerySet(UserQuerier, models.query.QuerySet):
    pass
