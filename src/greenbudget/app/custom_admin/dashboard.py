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
            )
        ))

        self.children.append(modules.ModelList(
            _('Templating'),
            column=1,
            collapsible=False,
            models=(
                'greenbudget.app.template.models.Template',
            )
        ))

        self.children.append(modules.ModelList(
            _('Tagging'),
            column=1,
            collapsible=False,
            models=(
                'greenbudget.app.tagging.models.Color',
                'greenbudget.app.subaccount.models.SubAccountUnit',
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
