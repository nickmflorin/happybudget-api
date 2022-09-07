from django.contrib.contenttypes.models import ContentType

from happybudget.app.tabling.query import (
    OrderedRowQuerier, OrderedRowQuerySet)
from happybudget.app.user.query import ModelOwnershipQuerier


class FringeQuerier(ModelOwnershipQuerier, OrderedRowQuerier):
    def for_budgets(self):
        # pylint: disable=import-outside-toplevel
        from happybudget.app.budget.models import Budget
        ctype_id = ContentType.objects.get_for_model(Budget).id
        return self.filter(budget__polymorphic_ctype_id=ctype_id)

    def for_templates(self):
        # pylint: disable=import-outside-toplevel
        from happybudget.app.template.models import Template
        ctype_id = ContentType.objects.get_for_model(Template).id
        return self.filter(budget__polymorphic_ctype_id=ctype_id)


class FringeQuerySet(FringeQuerier, OrderedRowQuerySet):
    pass
