from django.utils.translation import gettext_lazy as _
from grappelli.dashboard import modules, Dashboard as BaseDashboard


class Dashboard(BaseDashboard):
    template = "admin/dashboard.html"

    def init_with_context(self, context):
        self.children.append(modules.ModelList(
            _('Budgeting'),
            column=1,
            collapsible=False,
            models=(
                'happybudget.app.budget.models.Budget',
                'happybudget.app.account.models.BudgetAccount',
                'happybudget.app.group.models.BudgetGroup',
                'happybudget.app.subaccount.models.BudgetSubAccount',
                'happybudget.app.fringe.models.BudgetFringe',
            )
        ))

        self.children.append(modules.ModelList(
            _('Templating'),
            column=1,
            collapsible=False,
            models=(
                'happybudget.app.template.models.Template',
                'happybudget.app.account.models.TemplateAccount',
                'happybudget.app.group.models.TemplateGroup',
                'happybudget.app.subaccount.models.TemplateSubAccount',
                'happybudget.app.fringe.models.TemplateFringe',
            )
        ))

        self.children.append(modules.ModelList(
            _('Tagging'),
            column=1,
            collapsible=False,
            models=(
                'happybudget.app.tagging.models.Tag',
                'happybudget.app.tagging.models.Color',
                'happybudget.app.subaccount.models.SubAccountUnit',
                'happybudget.app.actual.models.ActualType',
            )
        ))

        self.children.append(modules.ModelList(
            _('Users'),
            column=1,
            collapsible=False,
            models=(
                'happybudget.app.user.models.User',
            )
        ))
