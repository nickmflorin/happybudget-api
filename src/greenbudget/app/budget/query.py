from django.db.models import Case, Q, When, Value as V, BooleanField

from greenbudget.app.budgeting.utils import get_instance_cls


class BudgetAncestorQuerier(object):
    def filter_by_budget(self, budget):
        """
        For some models, the model is only tied to a specific :obj:`BaseBudget`
        through it's ancestry trail, not directly.  For instance, in the case
        of the :obj:`group.models.Group`, the ancestry tree might look as
        follows:

        -- Budget
            -- Account
                -- SubAccount
                -- SubAccount
                    -- SubAccount
                    -- SubAccount
                    -- Group (parent = SubAccount)
                -- Group (parent = Account)
            -- Account
                -- SubAccount
                -- SubAccount
                -- Group (parent = Account)
            -- Group (parent = Budget)

        This method allows us to filter the model instances by the specific
        :obj:`BaseBudget` they are associated with at the top of the tree.

        Note:
        ----
        This method is slow, and query intensive, so it should be used
        sparingly.
        """
        return self.annotate(
            _ongoing=Case(
                When(self._get_case_query(budget), then=V(True)),
                default=V(False),
                output_field=BooleanField()
            )
        ).filter(_ongoing=True)

    def _get_case_query(self, budget):
        budget_ct = get_instance_cls(
            obj=budget,
            as_content_type=True,
            obj_type='budget'
        )
        account_ct = get_instance_cls(
            obj=budget,
            as_content_type=True,
            obj_type='account'
        )
        subaccount_ct = get_instance_cls(
            obj=budget,
            as_content_type=True,
            obj_type='subaccount'
        )
        accounts = [
            q[0] for q in account_ct.model_class().objects.filter(parent=budget)
            .only('pk').values_list('pk')
        ]
        subaccounts = [
            q[0] for q in subaccount_ct.model_class().objects
            .filter_by_budget(budget)
            .only('pk').values_list('pk')
        ]
        return (Q(content_type_id=budget_ct) & Q(object_id=budget.pk)) \
            | (Q(content_type_id=account_ct) & Q(object_id__in=accounts)) \
            | (Q(content_type_id=subaccount_ct) & Q(object_id__in=subaccounts))
