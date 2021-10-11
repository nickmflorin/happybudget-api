from django.utils.translation import gettext_lazy as _
from grappelli.dashboard import modules, Dashboard as BaseDashboard


class Dashboard(BaseDashboard):
    template = "custom_admin/dashboard.html"

    def init_with_context(self, context):
        self.children.append(modules.ModelList(
            _('Budgeting'),
            column=1,
            collapsible=False,
            models=(
                'greenbudget.app.budget.models.Budget',
                'greenbudget.app.account.models.BudgetAccount',
                # TODO: Filter by only those that are applicable.
                'greenbudget.app.group.models.Group',
                'greenbudget.app.subaccount.models.BudgetSubAccount',
                'greenbudget.app.fringe.models.BudgetFringe',
            )
        ))

        self.children.append(modules.ModelList(
            _('Templating'),
            column=1,
            collapsible=False,
            models=(
                'greenbudget.app.template.models.Template',
                'greenbudget.app.account.models.TemplateAccount',
                # TODO: Filter by only those that are applicable.
                'greenbudget.app.group.models.Group',
                'greenbudget.app.subaccount.models.TemplateSubAccount',
                'greenbudget.app.fringe.models.TemplateFringe',
            )
        ))

        self.children.append(modules.ModelList(
            _('Tagging'),
            column=1,
            collapsible=False,
            models=(
                'greenbudget.app.tagging.models.Tag',
                'greenbudget.app.tagging.models.Color',
                'greenbudget.app.subaccount.models.SubAccountUnit',
                'greenbudget.app.actual.models.ActualType',
            )
        ))

        self.children.append(modules.ModelList(
            _('Users'),
            column=1,
            collapsible=False,
            models=(
                'greenbudget.app.user.models.User',
            )
        ))
